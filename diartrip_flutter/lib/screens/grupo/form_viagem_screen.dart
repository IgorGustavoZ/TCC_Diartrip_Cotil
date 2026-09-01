import 'dart:async';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/web_style.dart';
import '../../providers/language_provider.dart';
import '../../services/geocode_service.dart';
import '../../services/grupo_service.dart';

enum _WizardPhase { asking, summary, editPick, creating }

class _ChatMsg {
  final String? text;
  final Map<String, dynamic>? summarySnapshot;
  final bool isUser;
  _ChatMsg.bot(String this.text)
      : isUser = false,
        summarySnapshot = null;
  _ChatMsg.user(String this.text)
      : isUser = true,
        summarySnapshot = null;
  _ChatMsg.summary(Map<String, dynamic> this.summarySnapshot)
      : isUser = false,
        text = null;
}

/// Assistente conversacional de criação de viagem, mirror de
/// backend/frontend/lobby-pags/chat-viagem.html: preenchimento sequencial
/// de campos via chat (slot-filling), com sugestão de cidade, resumo final
/// editável e criação via POST /grupos ao confirmar.
class FormViagemScreen extends StatefulWidget {
  const FormViagemScreen({super.key});
  @override
  State<FormViagemScreen> createState() => _FormViagemScreenState();
}

class _FormViagemScreenState extends State<FormViagemScreen> {
  static const _steps = [
    'nome', 'destino', 'data_inicio', 'data_fim',
    'participantes', 'orcamento', 'transporte', 'tipo', 'preferencias',
  ];

  static const _askKeys = {
    'nome': 'chatViagem.ask.nome',
    'destino': 'chatViagem.ask.destino',
    'data_inicio': 'chatViagem.ask.dataInicio',
    'data_fim': 'chatViagem.ask.dataFim',
    'participantes': 'chatViagem.ask.participantes',
    'orcamento': 'chatViagem.ask.orcamento',
    'transporte': 'chatViagem.ask.transporte',
    'tipo': 'chatViagem.ask.tipo',
    'preferencias': 'chatViagem.ask.preferencias',
  };

  static const _camposResumo = [
    ('nome', 'formViagem.name'),
    ('destino', 'formViagem.city'),
    ('data_inicio', 'formViagem.start'),
    ('data_fim', 'formViagem.end'),
    ('participantes', 'chatViagem.summary.participants'),
    ('orcamento', 'formViagem.budget'),
    ('transporte', 'chatViagem.summary.transport'),
    ('tipo', 'formViagem.type'),
    ('preferencias', 'formViagem.prefs.label'),
  ];

  // Slugs, não rótulos traduzidos — igual ao TIPOS de chat-viagem.html, para
  // o valor salvo não depender do idioma da UI no momento da criação.
  static const _tipos = [
    ('gastronomico', 'formViagem.type.gastronomic'),
    ('aventura', 'formViagem.type.adventure'),
    ('cultural', 'formViagem.type.cultural'),
    ('relax', 'formViagem.type.relax'),
  ];

  final _dados = <String, dynamic>{
    'nome': '', 'destino': '', 'data_inicio': '', 'data_fim': '',
    'participantes': '', 'orcamento': null, 'transporte': '', 'tipo': '', 'preferencias': '',
  };

  final List<_ChatMsg> _msgs = [];
  final _textCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final _fmt = DateFormat('yyyy-MM-dd');

  _WizardPhase _phase = _WizardPhase.asking;
  int _stepIndex = 0;
  bool _editingSingleField = false;
  DateTime? _pickedDate;
  List<String> _sugestoesCidade = [];
  String? _stepError;
  Timer? _debounce;
  Timer? _errorTimer;

  @override
  void initState() {
    super.initState();
    final lang = context.read<LanguageProvider>();
    _addBot(lang.translate('chatViagem.intro'));
    _askStep(_steps[0]);
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _errorTimer?.cancel();
    _textCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _addBot(String text) {
    setState(() => _msgs.add(_ChatMsg.bot(text)));
    _scrollDown();
  }

  void _addUser(String text) {
    setState(() => _msgs.add(_ChatMsg.user(text)));
    _scrollDown();
  }

  void _showStepError(String msgKey) {
    final lang = context.read<LanguageProvider>();
    _errorTimer?.cancel();
    setState(() => _stepError = lang.translate(msgKey));
    _errorTimer = Timer(const Duration(seconds: 3), () {
      if (mounted) setState(() => _stepError = null);
    });
  }

  void _askStep(String step) {
    final lang = context.read<LanguageProvider>();
    _addBot(lang.translate(_askKeys[step]!));

    if (step == 'data_inicio' || step == 'data_fim') {
      final existing = _dados[step] as String;
      _pickedDate = existing.isNotEmpty ? DateTime.tryParse(existing) : null;
    } else if (step == 'orcamento') {
      final v = _dados['orcamento'] as double?;
      _textCtrl.text = v != null ? v.toStringAsFixed(2) : '';
    } else if (step != 'tipo') {
      _textCtrl.text = (_dados[step] as String?) ?? '';
    }

    setState(() {
      _phase = _WizardPhase.asking;
      _stepIndex = _steps.indexOf(step);
      _sugestoesCidade = [];
      _stepError = null;
    });
  }

  void _afterAnswer() {
    if (_editingSingleField) {
      _editingSingleField = false;
      _renderSummary();
      return;
    }
    final next = _stepIndex + 1;
    if (next < _steps.length) {
      _askStep(_steps[next]);
    } else {
      _renderSummary();
    }
  }

  void _renderSummary() {
    setState(() {
      _msgs.add(_ChatMsg.summary(Map<String, dynamic>.from(_dados)));
      _phase = _WizardPhase.summary;
    });
    _scrollDown();
  }

  void _mostrarOpcoesEdicao() {
    final lang = context.read<LanguageProvider>();
    _addBot(lang.translate('chatViagem.editPick'));
    setState(() => _phase = _WizardPhase.editPick);
  }

  // ── Handlers por tipo de campo ────────────────────────────────────────

  void _submitText(String step, {required bool opcional}) {
    final lang = context.read<LanguageProvider>();
    final valor = _textCtrl.text.trim();
    if (!opcional && valor.isEmpty) {
      _showStepError('chatViagem.errNome');
      return;
    }
    _dados[step] = valor;
    _addUser(valor.isEmpty ? lang.translate('chatViagem.none') : valor);
    _afterAnswer();
  }

  void _skipText(String step) {
    final lang = context.read<LanguageProvider>();
    _dados[step] = '';
    _addUser(lang.translate('chatViagem.none'));
    _afterAnswer();
  }

  void _onDestinoChanged(String v) {
    _debounce?.cancel();
    if (v.trim().isEmpty) {
      setState(() => _sugestoesCidade = []);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 300), () async {
      final sugestoes = await GeocodeService.autocomplete(v);
      if (mounted) setState(() => _sugestoesCidade = sugestoes);
    });
  }

  void _selecionarCidade(String formatted) {
    _textCtrl.text = formatted;
    setState(() => _sugestoesCidade = []);
  }

  void _submitDestino() {
    final valor = _textCtrl.text.trim();
    if (valor.isEmpty) {
      _showStepError('chatViagem.errDestino');
      return;
    }
    _dados['destino'] = valor;
    setState(() => _sugestoesCidade = []);
    _addUser(valor);
    _afterAnswer();
  }

  Future<void> _escolherData(String step) async {
    final now = DateTime.now();
    final hoje = DateTime(now.year, now.month, now.day);
    final picked = await showDatePicker(
      context: context,
      initialDate: _pickedDate ?? hoje,
      firstDate: hoje,
      lastDate: DateTime(now.year + 5),
    );
    if (picked != null) setState(() => _pickedDate = picked);
  }

  void _submitData(String step) {
    if (_pickedDate == null) {
      _showStepError('chatViagem.errData');
      return;
    }
    final hoje = DateTime.now();
    final hojeSemHora = DateTime(hoje.year, hoje.month, hoje.day);
    if (_pickedDate!.isBefore(hojeSemHora)) {
      _showStepError('chatViagem.errData');
      return;
    }
    if (step == 'data_fim' && (_dados['data_inicio'] as String).isNotEmpty) {
      final inicio = DateTime.parse(_dados['data_inicio'] as String);
      if (!_pickedDate!.isAfter(inicio)) {
        _showStepError('chatViagem.errDataFim');
        return;
      }
    }
    final iso = _fmt.format(_pickedDate!);
    _dados[step] = iso;
    _addUser(iso);
    _afterAnswer();
  }

  void _submitOrcamento() {
    final valor = double.tryParse(_textCtrl.text.trim().replaceAll(',', '.'));
    if (valor == null || valor < 0) {
      _showStepError('formViagem.invalidBudget');
      return;
    }
    _dados['orcamento'] = valor;
    _addUser('R\$ ${valor.toStringAsFixed(2)}');
    _afterAnswer();
  }

  void _selecionarTipo(String valor, String labelKey) {
    final lang = context.read<LanguageProvider>();
    _dados['tipo'] = valor;
    _addUser(lang.translate(labelKey));
    _afterAnswer();
  }

  Future<void> _confirmarCriacao() async {
    final lang = context.read<LanguageProvider>();
    setState(() => _phase = _WizardPhase.creating);
    _addBot(lang.translate('chatViagem.creating'));

    final partes = <String>[];
    if ((_dados['participantes'] as String).isNotEmpty) {
      partes.add('${lang.translate('chatViagem.summary.participants')}: ${_dados['participantes']}');
    }
    if ((_dados['transporte'] as String).isNotEmpty) {
      partes.add('${lang.translate('chatViagem.summary.transport')}: ${_dados['transporte']}');
    }
    if ((_dados['preferencias'] as String).isNotEmpty) {
      partes.add(_dados['preferencias'] as String);
    }
    var preferenciasFinal = partes.join(' | ');
    if (preferenciasFinal.length > 1000) preferenciasFinal = preferenciasFinal.substring(0, 1000);

    try {
      await GrupoService.criar(
        nomeGrupo: _dados['nome'] as String,
        destinoPrincipal: _dados['destino'] as String,
        dataInicio: _dados['data_inicio'] as String,
        dataFim: _dados['data_fim'] as String,
        orcamento: (_dados['orcamento'] as double?) ?? 0,
        tipoViagem: _dados['tipo'] as String,
        preferencias: preferenciasFinal,
      );
      if (!mounted) return;
      _addBot(lang.translate('formViagem.success'));
      await Future.delayed(const Duration(milliseconds: 1200));
      if (mounted) Navigator.pushReplacementNamed(context, '/lobby');
    } catch (e) {
      if (!mounted) return;
      _addBot('${lang.translate('formViagem.error')} ($e)');
      _renderSummary();
    }
  }

  // ── UI ───────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return Scaffold(
      backgroundColor: WebColors.bg,
      appBar: AppBar(
        backgroundColor: WebColors.bg,
        elevation: 0,
        iconTheme: const IconThemeData(color: WebColors.textSecondary),
        title: Text(
          lang.translate('chatViagem.title'),
          style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 17),
        ),
      ),
      body: Stack(
        children: [
          const Positioned.fill(child: AmbientBackground()),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: GlassContainer(
                child: Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                      child: Row(
                        children: [
                          Text(
                            lang.translate('chatViagem.header'),
                            style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 14),
                          ),
                        ],
                      ),
                    ),
                    Divider(height: 1, color: WebColors.border),
                    Expanded(child: _buildMessages(lang)),
                    Padding(
                      padding: const EdgeInsets.all(14),
                      child: _buildInputArea(lang),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessages(LanguageProvider lang) {
    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.all(18),
      itemCount: _msgs.length,
      itemBuilder: (_, i) {
        final m = _msgs[i];
        if (m.summarySnapshot != null) return _summaryBubble(lang, m.summarySnapshot!);
        return _bubble(isUser: m.isUser, child: Text(
          m.text!,
          style: TextStyle(
            color: m.isUser ? Colors.white : WebColors.textSecondary,
            fontSize: 14,
            height: 1.5,
          ),
        ));
      },
    );
  }

  Widget _bubble({required bool isUser, required Widget child}) {
    final avatar = Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: isUser ? null : WebColors.gradient,
        color: isUser ? WebColors.surface2 : null,
      ),
      alignment: Alignment.center,
      child: Text(isUser ? '🧑' : '🤖', style: const TextStyle(fontSize: 15)),
    );
    final content = Container(
      constraints: const BoxConstraints(maxWidth: 340),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        gradient: isUser ? WebColors.gradient : null,
        color: isUser ? null : WebColors.surface2,
        borderRadius: isUser
            ? const BorderRadius.only(
                topLeft: Radius.circular(12), topRight: Radius.circular(4),
                bottomLeft: Radius.circular(12), bottomRight: Radius.circular(12))
            : const BorderRadius.only(
                topLeft: Radius.circular(4), topRight: Radius.circular(12),
                bottomLeft: Radius.circular(12), bottomRight: Radius.circular(12)),
      ),
      child: child,
    );
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: isUser
            ? [Flexible(child: content), const SizedBox(width: 10), avatar]
            : [avatar, const SizedBox(width: 10), Flexible(child: content)],
      ),
    );
  }

  Widget _summaryBubble(LanguageProvider lang, Map<String, dynamic> snap) {
    String valorFormatado(String campo) {
      final v = snap[campo];
      if (campo == 'orcamento') {
        return v != null ? 'R\$ ${(v as double).toStringAsFixed(2)}' : lang.translate('chatViagem.none');
      }
      if (campo == 'tipo') {
        final tipo = _tipos.where((t) => t.$1 == v);
        return tipo.isNotEmpty ? lang.translate(tipo.first.$2) : lang.translate('chatViagem.none');
      }
      final s = v as String?;
      return (s == null || s.isEmpty) ? lang.translate('chatViagem.none') : s;
    }

    return _bubble(
      isUser: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            lang.translate('chatViagem.summary.title'),
            style: const TextStyle(fontWeight: FontWeight.w700, color: WebColors.text, fontSize: 14),
          ),
          const SizedBox(height: 8),
          for (final (campo, labelKey) in _camposResumo)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 96,
                    child: Text(lang.translate(labelKey), style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
                  ),
                  Expanded(
                    child: Text(valorFormatado(campo), style: const TextStyle(color: WebColors.textSecondary, fontSize: 13)),
                  ),
                ],
              ),
            ),
          const SizedBox(height: 8),
          Text(lang.translate('chatViagem.summary.confirm'), style: const TextStyle(color: WebColors.textSecondary, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildInputArea(LanguageProvider lang) {
    switch (_phase) {
      case _WizardPhase.creating:
        return const SizedBox(
          height: 20,
          child: Center(child: SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2, color: WebColors.accent))),
        );
      case _WizardPhase.summary:
        return _quickReplies([
          (lang.translate('chatViagem.confirmBtn'), _confirmarCriacao),
          (lang.translate('chatViagem.editBtn'), _mostrarOpcoesEdicao),
        ]);
      case _WizardPhase.editPick:
        return _quickReplies([
          for (final c in _camposResumo)
            (lang.translate(c.$2), () {
              _editingSingleField = true;
              _askStep(c.$1);
            }),
        ]);
      case _WizardPhase.asking:
        return _buildStepInput(lang, _steps[_stepIndex]);
    }
  }

  Widget _quickReplies(List<(String, VoidCallback)> items) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final (label, onTap) in items)
          OutlinedButton(
            onPressed: onTap,
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: WebColors.border),
              backgroundColor: WebColors.surface,
              foregroundColor: WebColors.text,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            ),
            child: Text(label, style: const TextStyle(fontSize: 13)),
          ),
      ],
    );
  }

  Widget _pillTextField({
    required TextEditingController controller,
    String? hint,
    TextInputType? keyboardType,
    ValueChanged<String>? onChanged,
    ValueChanged<String>? onSubmitted,
  }) {
    return Container(
      height: 44,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: WebColors.surface2,
        borderRadius: BorderRadius.circular(WebColors.radiusPill),
        border: Border.all(color: WebColors.border),
      ),
      child: TextField(
        controller: controller,
        keyboardType: keyboardType,
        style: const TextStyle(color: WebColors.text, fontSize: 14),
        decoration: InputDecoration(
          filled: false,
          border: InputBorder.none,
          enabledBorder: InputBorder.none,
          focusedBorder: InputBorder.none,
          isCollapsed: true,
          hintText: hint,
          hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 14),
        ),
        onChanged: onChanged,
        onSubmitted: onSubmitted,
      ),
    );
  }

  Widget _sendBtn(VoidCallback onTap) => GradientButton(
        radius: WebColors.radiusPill,
        padding: const EdgeInsets.all(12),
        onPressed: onTap,
        child: const Icon(Icons.send_rounded, size: 18),
      );

  Widget _errorText(String msg) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(msg, style: const TextStyle(color: WebColors.danger, fontSize: 12)),
      );

  Widget _buildStepInput(LanguageProvider lang, String step) {
    if (step == 'tipo') {
      return _quickReplies([for (final t in _tipos) (lang.translate(t.$2), () => _selecionarTipo(t.$1, t.$2))]);
    }

    if (step == 'data_inicio' || step == 'data_fim') {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_stepError != null) _errorText(_stepError!),
          Row(
            children: [
              Expanded(
                child: GestureDetector(
                  onTap: () => _escolherData(step),
                  child: Container(
                    height: 44,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    alignment: Alignment.centerLeft,
                    decoration: BoxDecoration(
                      color: WebColors.surface2,
                      borderRadius: BorderRadius.circular(WebColors.radiusPill),
                      border: Border.all(color: WebColors.border),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.calendar_today, size: 15, color: WebColors.textMuted),
                        const SizedBox(width: 8),
                        Text(
                          _pickedDate != null
                              ? _fmt.format(_pickedDate!)
                              : lang.translate(step == 'data_inicio' ? 'formViagem.start' : 'formViagem.end'),
                          style: TextStyle(color: _pickedDate != null ? WebColors.text : WebColors.textMuted, fontSize: 14),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              _sendBtn(() => _submitData(step)),
            ],
          ),
        ],
      );
    }

    if (step == 'orcamento') {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_stepError != null) _errorText(_stepError!),
          Row(
            children: [
              Expanded(
                child: _pillTextField(
                  controller: _textCtrl,
                  hint: 'Ex: 3000.00',
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  onSubmitted: (_) => _submitOrcamento(),
                ),
              ),
              const SizedBox(width: 10),
              _sendBtn(_submitOrcamento),
            ],
          ),
        ],
      );
    }

    if (step == 'destino') {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_stepError != null) _errorText(_stepError!),
          if (_sugestoesCidade.isNotEmpty)
            Container(
              margin: const EdgeInsets.only(bottom: 8),
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
                  for (final s in _sugestoesCidade)
                    InkWell(
                      onTap: () => _selecionarCidade(s),
                      borderRadius: BorderRadius.circular(WebColors.radiusSm),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                        child: Text(s, style: const TextStyle(color: WebColors.textSecondary, fontSize: 13)),
                      ),
                    ),
                ],
              ),
            ),
          Row(
            children: [
              Expanded(
                child: _pillTextField(
                  controller: _textCtrl,
                  hint: lang.translate('formViagem.cityPlaceholder'),
                  onChanged: _onDestinoChanged,
                  onSubmitted: (_) => _submitDestino(),
                ),
              ),
              const SizedBox(width: 10),
              _sendBtn(_submitDestino),
            ],
          ),
        ],
      );
    }

    // Campos de texto genéricos: nome (obrigatório), participantes/transporte/preferencias (opcionais).
    final opcional = step != 'nome';
    const phKeys = {
      'nome': 'formViagem.name.placeholder',
      'participantes': 'chatViagem.ph.participantes',
      'transporte': 'chatViagem.ph.transporte',
      'preferencias': 'formViagem.prefs.placeholder',
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (_stepError != null) _errorText(_stepError!),
        Row(
          children: [
            Expanded(
              child: _pillTextField(
                controller: _textCtrl,
                hint: lang.translate(phKeys[step]!),
                onSubmitted: (_) => _submitText(step, opcional: opcional),
              ),
            ),
            const SizedBox(width: 10),
            _sendBtn(() => _submitText(step, opcional: opcional)),
            if (opcional) ...[
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: () => _skipText(step),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: WebColors.border),
                  foregroundColor: WebColors.textSecondary,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                ),
                child: Text(lang.translate('chatViagem.skip')),
              ),
            ],
          ],
        ),
      ],
    );
  }
}
