import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../../core/api_client.dart';
import '../../../core/web_style.dart';
import '../../../models/grupo.dart';
import '../../../providers/language_provider.dart';
import '../../../services/geocode_service.dart';
import '../../../services/grupo_service.dart';
import '../../../widgets/confirm_dialog.dart';

/// Aba "info" de viagem.html: dados da viagem, convite, dicas de IA e —
/// exclusivos do dono — configurações editáveis da viagem + zona de perigo
/// (sair/excluir).
class InfoTab extends StatefulWidget {
  final Grupo grupo;
  final int meId;
  final VoidCallback onReload;
  const InfoTab({super.key, required this.grupo, required this.meId, required this.onReload});

  @override
  State<InfoTab> createState() => _InfoTabState();
}

class _InfoTabState extends State<InfoTab> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  static final _dateFmt = DateFormat('yyyy-MM-dd');

  late final TextEditingController _nomeCtrl;
  late final TextEditingController _destinoCtrl;
  late final TextEditingController _tipoCtrl;
  late final TextEditingController _prefCtrl;
  DateTime? _dataInicio;
  DateTime? _dataFim;
  List<String> _sugestoesCidade = [];
  bool _salvando = false;
  bool _saindoOuExcluindo = false;
  String? _erroSettings;
  String? _sucessoSettings;

  bool get _souCriador => widget.grupo.criadorId == widget.meId;

  List<String> _aiTips(LanguageProvider lang) => [
        lang.translate('info.aiTip1'),
        lang.translate('info.aiTip2'),
        lang.translate('info.aiTip3'),
        lang.translate('info.aiTip4'),
        lang.translate('info.aiTip5'),
        lang.translate('info.aiTip6'),
      ];

  @override
  void initState() {
    super.initState();
    final g = widget.grupo;
    _nomeCtrl = TextEditingController(text: g.nomeGrupo);
    _destinoCtrl = TextEditingController(text: g.destinoPrincipal);
    _tipoCtrl = TextEditingController(text: g.tipoViagem ?? '');
    _prefCtrl = TextEditingController(text: g.preferencias ?? '');
    _dataInicio = g.dataInicio != null ? DateTime.tryParse(g.dataInicio!) : null;
    _dataFim = g.dataFim != null ? DateTime.tryParse(g.dataFim!) : null;
  }

  @override
  void dispose() {
    _nomeCtrl.dispose();
    _destinoCtrl.dispose();
    _tipoCtrl.dispose();
    _prefCtrl.dispose();
    super.dispose();
  }

  Future<void> _buscarCidade(String v) async {
    if (v.trim().isEmpty) {
      setState(() => _sugestoesCidade = []);
      return;
    }
    final s = await GeocodeService.autocomplete(v);
    if (mounted) setState(() => _sugestoesCidade = s);
  }

  Future<void> _pickData(bool inicio) async {
    final now = DateTime.now();
    final firstDate = DateTime(now.year - 2);
    final lastDate = DateTime(now.year + 5);
    // Datas de viagens antigas/distantes podem cair fora dessa janela —
    // showDatePicker exige initialDate dentro de [firstDate, lastDate].
    var initialDate = (inicio ? _dataInicio : _dataFim) ?? now;
    if (initialDate.isBefore(firstDate)) initialDate = firstDate;
    if (initialDate.isAfter(lastDate)) initialDate = lastDate;
    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: firstDate,
      lastDate: lastDate,
    );
    if (picked == null) return;
    setState(() {
      if (inicio) {
        _dataInicio = picked;
      } else {
        _dataFim = picked;
      }
    });
  }

  String? _validarDatas(bool dataMudou, LanguageProvider lang) {
    if (_dataInicio == null || _dataFim == null) return null;
    if (!_dataFim!.isAfter(_dataInicio!)) return lang.translate('viagem.settings.datesOrder');
    final hoje = DateTime.now();
    final hojeSemHora = DateTime(hoje.year, hoje.month, hoje.day);
    if (dataMudou && (_dataInicio!.isBefore(hojeSemHora) || _dataFim!.isBefore(hojeSemHora))) {
      return lang.translate('viagem.settings.datesPast');
    }
    return null;
  }

  Future<void> _salvarSettings() async {
    final lang = context.read<LanguageProvider>();
    setState(() {
      _erroSettings = null;
      _sucessoSettings = null;
    });
    final nome = _nomeCtrl.text.trim();
    final destino = _destinoCtrl.text.trim();
    final tipo = _tipoCtrl.text.trim();
    final pref = _prefCtrl.text.trim();
    if (nome.isEmpty || destino.isEmpty || _dataInicio == null || _dataFim == null || tipo.isEmpty) {
      setState(() => _erroSettings = lang.translate('viagem.settings.fillRequired'));
      return;
    }
    final dataInicioStr = _dateFmt.format(_dataInicio!);
    final dataFimStr = _dateFmt.format(_dataFim!);
    final dataMudou = dataInicioStr != widget.grupo.dataInicio || dataFimStr != widget.grupo.dataFim;
    final erroData = _validarDatas(dataMudou, lang);
    if (erroData != null) {
      setState(() => _erroSettings = erroData);
      return;
    }

    final infoRelevanteMudou = destino != widget.grupo.destinoPrincipal ||
        dataMudou ||
        tipo != (widget.grupo.tipoViagem ?? '') ||
        pref != (widget.grupo.preferencias ?? '');

    Future<void> executar() async {
      setState(() => _salvando = true);
      try {
        await GrupoService.atualizar(
          id: widget.grupo.id,
          nomeGrupo: nome,
          destinoPrincipal: destino,
          dataInicio: dataInicioStr,
          dataFim: dataFimStr,
          tipoViagem: tipo,
          preferencias: pref,
        );
        if (mounted) setState(() => _sucessoSettings = lang.translate('viagem.settings.saved'));
        widget.onReload();
      } catch (e) {
        if (mounted) {
          setState(() => _erroSettings = e is ApiException ? e.message : lang.translate('viagem.settings.error'));
        }
      } finally {
        if (mounted) setState(() => _salvando = false);
      }
    }

    if (infoRelevanteMudou) {
      final ok = await confirmarAcao(
        context,
        titulo: lang.translate('viagem.settings.destinationChangeTitle'),
        mensagem: lang.translate('viagem.settings.destinationChangeBody'),
        textoConfirmar: lang.translate('viagem.settings.destinationChangeConfirm'),
      );
      if (!ok) return;
    }
    await executar();
  }

  Future<void> _sair() async {
    final lang = context.read<LanguageProvider>();
    final ok = await confirmarAcao(
      context,
      titulo: lang.translate('viagem.leaveConfirmTitle'),
      mensagem: lang.translate('viagem.leaveConfirmBody'),
      textoConfirmar: lang.translate('viagem.leaveTrip'),
    );
    if (!ok) return;
    setState(() => _saindoOuExcluindo = true);
    try {
      await GrupoService.sair(widget.grupo.id);
      if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/lobby', (_) => false);
    } catch (e) {
      if (mounted) {
        setState(() => _saindoOuExcluindo = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e is ApiException ? e.message : lang.translate('viagem.leaveError'))),
        );
      }
    }
  }

  Future<void> _excluir() async {
    final lang = context.read<LanguageProvider>();
    final ok = await confirmarAcao(
      context,
      titulo: lang.translate('viagem.deleteConfirmTitle'),
      mensagem: lang.translate('viagem.deleteConfirmBody'),
      textoConfirmar: lang.translate('viagem.deleteTrip'),
    );
    if (!ok) return;
    setState(() => _saindoOuExcluindo = true);
    try {
      await GrupoService.deletar(widget.grupo.id);
      if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/lobby', (_) => false);
    } catch (e) {
      if (mounted) {
        setState(() => _saindoOuExcluindo = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e is ApiException ? e.message : lang.translate('viagem.deleteError'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final lang = context.watch<LanguageProvider>();
    final g = widget.grupo;
    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 0, 14, 24),
      children: [
        // Info + Convite + Dicas de IA moram no mesmo card (com divisórias
        // internas) em vez de 3 cards separados: cada `TripCardExpanded` traz
        // seu próprio `BackdropFilter`, e empilhar muitos é uma fonte real de
        // lentidão/engasgo na web — juntar esses três, puramente
        // informativos, corta os blurs simultâneos pela metade sem esconder
        // nenhum conteúdo.
        TripCardExpanded(
          title: '📌 ${lang.translate('viagem.infoTitle')}',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _infoItem(lang.translate('info.destination'), g.destinoPrincipal),
              if (g.dataInicio != null)
                _infoItem(lang.translate('info.period'), '${g.dataInicio} → ${g.dataFim ?? '?'}'),
              if (g.codigoConvite != null) _infoItem(lang.translate('info.inviteCode'), g.codigoConvite!),
              if (g.codigoConvite != null) ...[
                const SizedBox(height: 16),
                Divider(color: WebColors.border, height: 1),
                const SizedBox(height: 16),
                _sectionHeading('👥 ${lang.translate('viagem.inviteTitle')}'),
                const SizedBox(height: 8),
                Text(lang.translate('viagem.inviteDesc'), style: const TextStyle(color: WebColors.textMuted, fontSize: 13)),
                const SizedBox(height: 12),
                _inviteBox(lang),
              ],
              const SizedBox(height: 16),
              Divider(color: WebColors.border, height: 1),
              const SizedBox(height: 16),
              _sectionHeading('🤖 ${lang.translate('info.aiTipsTitle')}'),
              const SizedBox(height: 8),
              Text(lang.translate('info.aiTipsSubtitle'),
                  style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
              const SizedBox(height: 10),
              ..._aiTips(lang).map((tip) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('💬', style: TextStyle(fontSize: 12)),
                        const SizedBox(width: 8),
                        Expanded(child: Text(tip, style: const TextStyle(fontSize: 13, color: WebColors.textSecondary))),
                      ],
                    ),
                  )),
            ],
          ),
        ),
        if (_souCriador) TripCardExpanded(title: lang.translate('viagem.settings.title'), child: _settingsForm(lang)),
        TripCardExpanded(
          title: lang.translate('viagem.dangerZone'),
          titleColor: WebColors.danger,
          borderColor: WebColors.danger.withValues(alpha: 0.3),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _souCriador ? lang.translate('viagem.dangerZone.ownerDesc') : lang.translate('viagem.dangerZone.memberDesc'),
                style: const TextStyle(color: WebColors.textMuted, fontSize: 13, height: 1.4),
              ),
              const SizedBox(height: 14),
              OutlinedButton(
                onPressed: _saindoOuExcluindo ? null : (_souCriador ? _excluir : _sair),
                style: OutlinedButton.styleFrom(
                  foregroundColor: WebColors.danger,
                  side: BorderSide(color: WebColors.danger.withValues(alpha: 0.35)),
                  backgroundColor: _souCriador ? WebColors.danger : null,
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 11),
                ),
                child: _saindoOuExcluindo
                    ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2, color: WebColors.danger))
                    : Text(
                        _souCriador ? lang.translate('viagem.deleteTrip') : lang.translate('viagem.leaveTrip'),
                        style: TextStyle(color: _souCriador ? Colors.white : WebColors.danger, fontWeight: FontWeight.w700),
                      ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _sectionHeading(String text) => Text(
        text,
        style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 15),
      );

  Widget _infoItem(String label, String value) => Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: WebColors.border))),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(color: WebColors.textSecondary, fontSize: 14)),
            Flexible(
              child: Text(value,
                  textAlign: TextAlign.right,
                  style: const TextStyle(color: WebColors.text, fontSize: 15, fontWeight: FontWeight.w600)),
            ),
          ],
        ),
      );

  Widget _inviteBox(LanguageProvider lang) {
    final codigo = widget.grupo.codigoConvite ?? '';
    return Row(
      children: [
        Expanded(
          child: Container(
            height: 44,
            padding: const EdgeInsets.symmetric(horizontal: 14),
            alignment: Alignment.centerLeft,
            decoration: BoxDecoration(
              color: WebColors.surface2,
              borderRadius: BorderRadius.circular(WebColors.radiusMd),
              border: Border.all(color: WebColors.border),
            ),
            child: Text(codigo,
                style: const TextStyle(
                    color: WebColors.text, fontFamily: 'monospace', fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 2)),
          ),
        ),
        const SizedBox(width: 10),
        GradientButton(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          onPressed: () {
            Clipboard.setData(ClipboardData(text: codigo));
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(lang.translate('info.codeCopied'))));
          },
          child: Text(lang.translate('common.copy'), style: const TextStyle(fontSize: 13)),
        ),
      ],
    );
  }

  Widget _settingsForm(LanguageProvider lang) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _label(lang.translate('viagem.settings.name')),
        _textField(_nomeCtrl),
        const SizedBox(height: 12),
        _label(lang.translate('viagem.settings.destination')),
        _textField(_destinoCtrl, onChanged: _buscarCidade),
        if (_sugestoesCidade.isNotEmpty)
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
                for (final s in _sugestoesCidade)
                  InkWell(
                    onTap: () {
                      _destinoCtrl.text = s;
                      setState(() => _sugestoesCidade = []);
                    },
                    borderRadius: BorderRadius.circular(WebColors.radiusSm),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                      child: Text(s, style: const TextStyle(color: WebColors.textSecondary, fontSize: 13)),
                    ),
                  ),
              ],
            ),
          ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _label(lang.translate('viagem.settings.startDate')),
                  _dateBtn(_dataInicio, () => _pickData(true)),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _label(lang.translate('viagem.settings.endDate')),
                  _dateBtn(_dataFim, () => _pickData(false)),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _label(lang.translate('viagem.settings.type')),
        _textField(_tipoCtrl),
        const SizedBox(height: 12),
        _label(lang.translate('viagem.settings.preferences')),
        _textField(_prefCtrl, maxLines: 3),
        const SizedBox(height: 14),
        GradientButton(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          onPressed: _salvando ? null : _salvarSettings,
          child: _salvando
              ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : Text(lang.translate('viagem.settings.save'), style: const TextStyle(fontSize: 13)),
        ),
        if (_erroSettings != null) ...[
          const SizedBox(height: 8),
          Text(_erroSettings!, style: const TextStyle(color: WebColors.danger, fontSize: 12)),
        ],
        if (_sucessoSettings != null) ...[
          const SizedBox(height: 8),
          Text(_sucessoSettings!, style: const TextStyle(color: WebColors.success, fontSize: 12)),
        ],
      ],
    );
  }

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Text(text, style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
      );

  Widget _textField(TextEditingController ctrl, {int maxLines = 1, ValueChanged<String>? onChanged}) {
    return TextField(
      controller: ctrl,
      maxLines: maxLines,
      onChanged: onChanged,
      style: const TextStyle(color: WebColors.text, fontSize: 14),
      decoration: InputDecoration(
        filled: true,
        fillColor: WebColors.surface2,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(WebColors.radiusSm),
          borderSide: const BorderSide(color: WebColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(WebColors.radiusSm),
          borderSide: const BorderSide(color: WebColors.border),
        ),
      ),
    );
  }

  Widget _dateBtn(DateTime? date, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(WebColors.radiusSm),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
        decoration: BoxDecoration(
          color: WebColors.surface2,
          borderRadius: BorderRadius.circular(WebColors.radiusSm),
          border: Border.all(color: WebColors.border),
        ),
        child: Row(
          children: [
            const Icon(Icons.calendar_today_outlined, size: 14, color: WebColors.textMuted),
            const SizedBox(width: 8),
            Text(
              date != null ? _dateFmt.format(date) : '—',
              style: const TextStyle(color: WebColors.text, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }
}
