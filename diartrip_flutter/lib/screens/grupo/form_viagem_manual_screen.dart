import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/web_style.dart';
import '../../providers/language_provider.dart';
import '../../services/geocode_service.dart';
import '../../services/grupo_service.dart';

/// Monta o campo `preferencias` enviado ao backend. O gerador de roteiro por IA
/// (`roteiro_ia_service._extrair_preferencias`) só reconhece os rótulos
/// "Participantes: N" e "Transporte: X" em português, por isso eles NÃO são
/// traduzidos — o resto vira "interesses" (texto livre). Limite de 1000 chars.
String montarPreferenciasViagem({
  String participantes = '',
  String transporte = '',
  String preferencias = '',
}) {
  final partes = <String>[];
  if (participantes.trim().isNotEmpty) partes.add('Participantes: ${participantes.trim()}');
  if (transporte.trim().isNotEmpty) partes.add('Transporte: ${transporte.trim()}');
  if (preferencias.trim().isNotEmpty) partes.add(preferencias.trim());
  final texto = partes.join(' | ');
  return texto.length > 1000 ? texto.substring(0, 1000) : texto;
}

/// Criação de viagem por formulário (preenchimento manual), mirror de
/// backend/frontend/lobby-pags/form-viagem.html — mesmas regras de validação e
/// o mesmo POST /grupos do assistente em chat ([FormViagemScreen]), que continua
/// sendo a tela padrão de "nova viagem".
class FormViagemManualScreen extends StatefulWidget {
  const FormViagemManualScreen({super.key});
  @override
  State<FormViagemManualScreen> createState() => _FormViagemManualScreenState();
}

class _FormViagemManualScreenState extends State<FormViagemManualScreen> {
  // Slugs, não rótulos traduzidos — igual ao assistente (o valor salvo não
  // depende do idioma da UI no momento da criação).
  static const _tipos = [
    ('gastronomico', 'formViagem.type.gastronomic'),
    ('aventura', 'formViagem.type.adventure'),
    ('cultural', 'formViagem.type.cultural'),
    ('relax', 'formViagem.type.relax'),
  ];

  final _nomeCtrl = TextEditingController();
  final _destinoCtrl = TextEditingController();
  final _orcCtrl = TextEditingController();
  final _partCtrl = TextEditingController();
  final _transpCtrl = TextEditingController();
  final _prefCtrl = TextEditingController();
  final _fmt = DateFormat('yyyy-MM-dd');

  DateTime? _inicio;
  DateTime? _fim;
  String? _tipo;
  List<String> _sugestoes = [];
  Timer? _debounce;
  String? _erro;
  String? _sucesso;
  bool _criando = false;

  @override
  void dispose() {
    _debounce?.cancel();
    _nomeCtrl.dispose();
    _destinoCtrl.dispose();
    _orcCtrl.dispose();
    _partCtrl.dispose();
    _transpCtrl.dispose();
    _prefCtrl.dispose();
    super.dispose();
  }

  DateTime get _hoje {
    final n = DateTime.now();
    return DateTime(n.year, n.month, n.day);
  }

  void _onDestinoChanged(String v) {
    _debounce?.cancel();
    if (v.trim().isEmpty) {
      setState(() => _sugestoes = []);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 300), () async {
      final s = await GeocodeService.autocomplete(v);
      if (mounted) setState(() => _sugestoes = s);
    });
  }

  Future<void> _escolherData({required bool inicio}) async {
    final hoje = _hoje;
    // O fim só pode ser depois do início (mesma regra do site e do assistente).
    final primeira = inicio ? hoje : (_inicio?.add(const Duration(days: 1)) ?? hoje);
    final atual = inicio ? _inicio : _fim;
    final picked = await showDatePicker(
      context: context,
      initialDate: (atual != null && !atual.isBefore(primeira)) ? atual : primeira,
      firstDate: primeira,
      lastDate: DateTime(hoje.year + 5),
    );
    if (picked == null || !mounted) return;
    setState(() {
      if (inicio) {
        _inicio = picked;
        // Se o início passou a ser depois/igual ao fim, o fim precisa ser escolhido de novo.
        if (_fim != null && !_fim!.isAfter(picked)) _fim = null;
      } else {
        _fim = picked;
      }
    });
  }

  Future<void> _criar() async {
    final lang = context.read<LanguageProvider>();
    final nome = _nomeCtrl.text.trim();
    final destino = _destinoCtrl.text.trim();
    int? participantes = int.tryParse(_partCtrl.text);

    String? erro;
    if (nome.isEmpty || destino.isEmpty || _inicio == null || _fim == null || _tipo == null) {
      erro = lang.translate('formViagem.fillAll');
    }
    final orcamento = double.tryParse(_orcCtrl.text.trim().replaceAll(',', '.'));
    if (erro == null && (orcamento == null || orcamento < 0)) {
      erro = lang.translate('formViagem.invalidBudget');
    }
    // Participantes é opcional: só valida se a pessoa preencheu, e não
    // sobrescreve um erro anterior (campos obrigatórios/orçamento).
    if (erro == null && _partCtrl.text.trim().isNotEmpty && (participantes == null || participantes < 0)) {
      erro = lang.translate('formViagem.invalidInfo');
    }
    if (erro == null) {
      final hoje = _hoje;
      if (_inicio!.isBefore(hoje) || _fim!.isBefore(hoje) || !_fim!.isAfter(_inicio!)) {
        erro = lang.translate('formViagem.invalidInfo');
      }
    }
    if (erro != null) {
      setState(() { _erro = erro; _sucesso = null; });
      return;
    }

    setState(() { _criando = true; _erro = null; _sucesso = null; });
    try {
      await GrupoService.criar(
        nomeGrupo: nome,
        destinoPrincipal: destino,
        dataInicio: _fmt.format(_inicio!),
        dataFim: _fmt.format(_fim!),
        orcamento: orcamento!,
        tipoViagem: _tipo!,
        preferencias: montarPreferenciasViagem(
          participantes: _partCtrl.text,
          transporte: _transpCtrl.text,
          preferencias: _prefCtrl.text,
        ),
      );
      if (!mounted) return;
      setState(() => _sucesso = lang.translate('formViagem.success'));
      await Future.delayed(const Duration(milliseconds: 1200));
      if (mounted) Navigator.pushReplacementNamed(context, '/lobby');
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _erro = '${lang.translate('formViagem.error')} (${e.toString().replaceFirst('Exception: ', '')})';
        _criando = false;
      });
    }
  }

  // ── UI ───────────────────────────────────────────────────────────────

  InputDecoration _dec(String hint) {
    OutlineInputBorder borda(Color c, [double w = 1]) => OutlineInputBorder(
          borderRadius: BorderRadius.circular(WebColors.radiusMd),
          borderSide: BorderSide(color: c, width: w),
        );
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 14),
      filled: true,
      fillColor: WebColors.surface2,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      enabledBorder: borda(WebColors.border),
      focusedBorder: borda(WebColors.primary, 1.5),
    );
  }

  Widget _campo(String label, Widget input) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(color: WebColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 6),
          input,
        ],
      );

  Widget _campoData(LanguageProvider lang, {required bool inicio}) {
    final data = inicio ? _inicio : _fim;
    return _campo(
      lang.translate(inicio ? 'formViagem.start' : 'formViagem.end'),
      InkWell(
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
        onTap: () => _escolherData(inicio: inicio),
        child: Container(
          height: 48,
          padding: const EdgeInsets.symmetric(horizontal: 14),
          alignment: Alignment.centerLeft,
          decoration: BoxDecoration(
            color: WebColors.surface2,
            borderRadius: BorderRadius.circular(WebColors.radiusMd),
            border: Border.all(color: WebColors.border),
          ),
          child: Row(
            children: [
              const Icon(Icons.calendar_today, size: 15, color: WebColors.textMuted),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  data != null ? _fmt.format(data) : 'aaaa-mm-dd',
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: data != null ? WebColors.text : WebColors.textMuted,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    const estiloTexto = TextStyle(color: WebColors.text, fontSize: 14);
    final opcional = ' ${lang.translate('formViagem.optional')}';

    return Scaffold(
      backgroundColor: WebColors.bg,
      appBar: AppBar(
        backgroundColor: WebColors.bg,
        elevation: 0,
        iconTheme: const IconThemeData(color: WebColors.textSecondary),
        title: Text(
          lang.translate('formViagem.manualTitle'),
          style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 17),
        ),
      ),
      body: Stack(
        children: [
          const Positioned.fill(child: AmbientBackground()),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 560),
                  child: GlassContainer(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Alternativa: voltar ao assistente em formato de chat.
                        _faixaTroca(
                          hint: lang.translate('formViagem.assistantHint'),
                          botao: lang.translate('formViagem.assistantBtn'),
                          icone: Icons.chat_bubble_outline,
                          rota: '/nova-viagem',
                        ),
                        const SizedBox(height: 18),
                        Text(
                          lang.translate('formViagem.manualHeader'),
                          style: const TextStyle(color: WebColors.text, fontSize: 16, fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 16),
                        _campo(
                          lang.translate('formViagem.name'),
                          TextField(
                            controller: _nomeCtrl,
                            style: estiloTexto,
                            cursorColor: WebColors.primary,
                            textInputAction: TextInputAction.next,
                            decoration: _dec(lang.translate('formViagem.name.placeholder')),
                          ),
                        ),
                        const SizedBox(height: 16),
                        _campo(
                          lang.translate('formViagem.city'),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              TextField(
                                controller: _destinoCtrl,
                                style: estiloTexto,
                                cursorColor: WebColors.primary,
                                textInputAction: TextInputAction.next,
                                onChanged: _onDestinoChanged,
                                decoration: _dec(lang.translate('formViagem.cityPlaceholder')),
                              ),
                              if (_sugestoes.isNotEmpty)
                                Container(
                                  margin: const EdgeInsets.only(top: 6),
                                  constraints: const BoxConstraints(maxHeight: 160),
                                  decoration: BoxDecoration(
                                    color: WebColors.surface,
                                    border: Border.all(color: WebColors.border),
                                    borderRadius: BorderRadius.circular(WebColors.radiusMd),
                                  ),
                                  child: ListView(
                                    shrinkWrap: true,
                                    padding: const EdgeInsets.all(6),
                                    children: [
                                      for (final s in _sugestoes)
                                        InkWell(
                                          onTap: () {
                                            _destinoCtrl.text = s;
                                            setState(() => _sugestoes = []);
                                          },
                                          borderRadius: BorderRadius.circular(WebColors.radiusSm),
                                          child: Padding(
                                            padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                                            child: Text(
                                              s,
                                              style: const TextStyle(color: WebColors.textSecondary, fontSize: 13),
                                            ),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(child: _campoData(lang, inicio: true)),
                            const SizedBox(width: 12),
                            Expanded(child: _campoData(lang, inicio: false)),
                          ],
                        ),
                        const SizedBox(height: 16),
                        _campo(
                          lang.translate('formViagem.budget'),
                          TextField(
                            controller: _orcCtrl,
                            style: estiloTexto,
                            cursorColor: WebColors.primary,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            textInputAction: TextInputAction.next,
                            decoration: _dec('Ex: 3000.00'),
                          ),
                        ),
                        const SizedBox(height: 16),
                        _campo(
                          lang.translate('formViagem.type'),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              for (final t in _tipos)
                                ChoiceChip(
                                  label: Text(lang.translate(t.$2)),
                                  selected: _tipo == t.$1,
                                  onSelected: (_) => setState(() => _tipo = t.$1),
                                  showCheckmark: false,
                                  labelStyle: TextStyle(
                                    color: _tipo == t.$1 ? Colors.white : WebColors.textSecondary,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                  ),
                                  backgroundColor: WebColors.surface2,
                                  selectedColor: WebColors.primary,
                                  side: BorderSide(color: _tipo == t.$1 ? WebColors.primary : WebColors.border),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                                ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: _campo(
                                '${lang.translate('chatViagem.summary.participants')}$opcional',
                                TextField(
                                  controller: _partCtrl,
                                  style: estiloTexto,
                                  cursorColor: WebColors.primary,
                                  keyboardType: TextInputType.number,
                                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                                  textInputAction: TextInputAction.next,
                                  decoration: _dec(lang.translate('chatViagem.ph.participantes')),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: _campo(
                                '${lang.translate('chatViagem.summary.transport')}$opcional',
                                TextField(
                                  controller: _transpCtrl,
                                  style: estiloTexto,
                                  cursorColor: WebColors.primary,
                                  textInputAction: TextInputAction.next,
                                  decoration: _dec(lang.translate('chatViagem.ph.transporte')),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        _campo(
                          '${lang.translate('formViagem.prefs.label')}$opcional',
                          TextField(
                            controller: _prefCtrl,
                            style: estiloTexto,
                            cursorColor: WebColors.primary,
                            textInputAction: TextInputAction.done,
                            decoration: _dec(lang.translate('formViagem.prefs.placeholder')),
                          ),
                        ),
                        if (_erro != null) ...[
                          const SizedBox(height: 14),
                          Text(_erro!, style: const TextStyle(color: WebColors.danger, fontSize: 13)),
                        ],
                        if (_sucesso != null) ...[
                          const SizedBox(height: 14),
                          Text(_sucesso!, style: const TextStyle(color: WebColors.success, fontSize: 13)),
                        ],
                        const SizedBox(height: 20),
                        GradientButton(
                          radius: WebColors.radiusPill,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          onPressed: _criando ? null : _criar,
                          child: Center(
                            child: _criando
                                ? const SizedBox(
                                    height: 18,
                                    width: 18,
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                  )
                                : Text(lang.translate('formViagem.submit')),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _faixaTroca({
    required String hint,
    required String botao,
    required IconData icone,
    required String rota,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      decoration: BoxDecoration(
        color: WebColors.surface2,
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
        border: Border.all(color: WebColors.border),
      ),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 8,
        children: [
          Text(hint, style: const TextStyle(color: WebColors.textMuted, fontSize: 13)),
          TextButton.icon(
            onPressed: _criando ? null : () => Navigator.pushReplacementNamed(context, rota),
            icon: Icon(icone, size: 16),
            label: Text(botao),
            style: TextButton.styleFrom(
              foregroundColor: WebColors.accent,
              visualDensity: VisualDensity.compact,
              textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
