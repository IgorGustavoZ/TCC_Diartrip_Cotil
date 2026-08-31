import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/api_client.dart';
import '../../../core/app_logger.dart';
import '../../../core/web_style.dart';
import '../../../models/roteiro.dart';
import '../../../providers/language_provider.dart';
import '../../../services/roteiro_service.dart';
import '../../../widgets/confirm_dialog.dart';

/// Aba "roteiro" de viagem.html: lista de itens do roteiro, com geração via
/// IA e edição inline (admin) — igual a `gerarRoteiroComIA()`/`carregarRoteiro()`.
class ItineraryTab extends StatefulWidget {
  final int idGrupo;
  final bool isAdmin;
  /// Recarrega o dashboard compartilhado no [ViagemScreen] — o painel Admin
  /// mostra a contagem de itens do roteiro, que fica desatualizada sem isso.
  final Future<void> Function() onReload;
  const ItineraryTab({super.key, required this.idGrupo, required this.isAdmin, required this.onReload});
  @override
  State<ItineraryTab> createState() => _ItineraryTabState();
}

class _ItineraryTabState extends State<ItineraryTab>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;
  List<Roteiro> _roteiros = [];
  bool _loading = true;
  bool _gerandoIA = false;
  int? _editandoId;
  Timer? _statusTimer;
  String _statusIA = '';

  final Map<int, TextEditingController> _tituloCtrls = {};
  final Map<int, TextEditingController> _descCtrls = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _statusTimer?.cancel();
    for (final c in _tituloCtrls.values) {
      c.dispose();
    }
    for (final c in _descCtrls.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final r = await RoteiroService.listar(widget.idGrupo);
      if (mounted) setState(() { _roteiros = r; _loading = false; });
    } catch (e, s) {
      AppLogger.captureError('ItineraryTab._load', e, s);
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _gerarComIA() async {
    final lang = context.read<LanguageProvider>();
    final mensagens = [
      lang.translate('viagem.itinerary.ia.step1'),
      lang.translate('viagem.itinerary.ia.step2'),
      lang.translate('viagem.itinerary.ia.step3'),
      lang.translate('viagem.itinerary.ia.step4'),
    ];
    setState(() {
      _gerandoIA = true;
      _statusIA = mensagens[0];
    });
    var i = 0;
    _statusTimer = Timer.periodic(const Duration(milliseconds: 1800), (_) {
      i = (i + 1) % mensagens.length;
      if (mounted) setState(() => _statusIA = mensagens[i]);
    });
    try {
      final novos = await RoteiroService.gerarIA(widget.idGrupo);
      if (mounted) setState(() => _roteiros = novos);
      await widget.onReload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e is ApiException ? e.message : lang.translate('viagem.itinerary.ia.error'))),
        );
      }
    } finally {
      _statusTimer?.cancel();
      if (mounted) setState(() => _gerandoIA = false);
    }
  }

  Future<void> _showAddForm() async {
    final lang = context.read<LanguageProvider>();
    final tituloCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    String? erro;
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (ctx, setDialog) => AlertDialog(
          backgroundColor: WebColors.bg2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(WebColors.radiusLg)),
          title: Text(lang.translate('itinerary.add'), style: const TextStyle(color: WebColors.text)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _dialogField(tituloCtrl, lang.translate('itinerary.title'), autofocus: true),
              const SizedBox(height: 10),
              _dialogField(descCtrl, lang.translate('itinerary.description'), maxLines: 3),
              if (erro != null) ...[
                const SizedBox(height: 8),
                Text(erro!, style: const TextStyle(color: WebColors.danger, fontSize: 12)),
              ],
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                style: TextButton.styleFrom(foregroundColor: WebColors.textMuted),
                child: Text(lang.translate('itinerary.cancel'))),
            TextButton(
              onPressed: () {
                if (tituloCtrl.text.trim().isEmpty) {
                  setDialog(() => erro = lang.translate('viagem.itinerary.titleError'));
                  return;
                }
                Navigator.pop(ctx, true);
              },
              style: TextButton.styleFrom(foregroundColor: WebColors.primary),
              child: Text(lang.translate('itinerary.save'), style: const TextStyle(fontWeight: FontWeight.w700)),
            ),
          ],
        ),
      ),
    );
    if (ok != true) return;
    final titulo = tituloCtrl.text.trim();
    final desc = descCtrl.text.trim();
    if (titulo.isEmpty) return;
    try {
      await RoteiroService.criar(idGrupo: widget.idGrupo, titulo: titulo, descricao: desc);
      await _load();
      await widget.onReload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  void _iniciarEdicao(Roteiro r) {
    _tituloCtrls[r.id] = TextEditingController(text: r.titulo);
    _descCtrls[r.id] = TextEditingController(text: r.descricao);
    setState(() => _editandoId = r.id);
  }

  Future<void> _salvarEdicao(int id) async {
    final titulo = _tituloCtrls[id]!.text.trim();
    final desc = _descCtrls[id]!.text.trim();
    if (titulo.isEmpty) return;
    try {
      await RoteiroService.atualizar(id: id, titulo: titulo, descricao: desc);
      setState(() => _editandoId = null);
      _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  Future<void> _deletar(Roteiro r) async {
    final lang = context.read<LanguageProvider>();
    final ok = await confirmarAcao(
      context,
      titulo: lang.translate('viagem.itinerary.deleteConfirmTitle'),
      mensagem: lang.translate('viagem.itinerary.deleteConfirmBody'),
      textoConfirmar: lang.translate('viagem.itinerary.deleteConfirmBtn'),
    );
    if (!ok) return;
    try {
      await RoteiroService.deletar(r.id);
      await _load();
      await widget.onReload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  InputDecoration _dialogDecoration(String label) => InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: WebColors.textMuted, fontSize: 13),
        filled: true,
        fillColor: WebColors.surface2,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(WebColors.radiusSm), borderSide: const BorderSide(color: WebColors.border)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(WebColors.radiusSm), borderSide: const BorderSide(color: WebColors.border)),
      );

  Widget _dialogField(TextEditingController ctrl, String label, {int maxLines = 1, bool autofocus = false}) => TextField(
        controller: ctrl,
        maxLines: maxLines,
        autofocus: autofocus,
        style: const TextStyle(color: WebColors.text, fontSize: 14),
        decoration: _dialogDecoration(label),
      );

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final lang = context.watch<LanguageProvider>();
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: widget.isAdmin
          ? FloatingActionButton(
              mini: true,
              backgroundColor: WebColors.primary,
              onPressed: _showAddForm,
              child: const Icon(Icons.add),
            )
          : null,
      body: ListView(
        padding: const EdgeInsets.fromLTRB(14, 0, 14, 80),
        children: [
          TripCardExpanded(
            title: '📋 ${lang.translate('viagem.itineraryTitle')}',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (widget.isAdmin) ...[
                  Row(
                    children: [
                      Flexible(
                        child: OutlinedButton(
                          onPressed: _gerandoIA ? null : _gerarComIA,
                          style: OutlinedButton.styleFrom(
                            foregroundColor: WebColors.violet,
                            side: BorderSide(color: WebColors.violet.withValues(alpha: 0.4)),
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          ),
                          child: _gerandoIA
                              ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2, color: WebColors.violet))
                              : Text(
                                  _roteiros.isNotEmpty
                                      ? lang.translate('viagem.itinerary.ia.regenerateBtn')
                                      : lang.translate('viagem.itinerary.ia.createBtn'),
                                  style: const TextStyle(fontSize: 13),
                                  overflow: TextOverflow.ellipsis,
                                ),
                        ),
                      ),
                      if (_gerandoIA) ...[
                        const SizedBox(width: 10),
                        Flexible(child: Text(_statusIA, style: const TextStyle(color: WebColors.textMuted, fontSize: 12))),
                      ],
                    ],
                  ),
                  const SizedBox(height: 16),
                ],
                if (_loading)
                  const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator(color: WebColors.primary)))
                else if (_roteiros.isEmpty)
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 30),
                      child: Text(lang.translate('itinerary.empty'), style: const TextStyle(color: WebColors.textMuted, fontSize: 14)),
                    ),
                  )
                else
                  Column(
                    children: List.generate(_roteiros.length, (i) => _itemCard(context, lang, _roteiros[i], i)),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _itemCard(BuildContext context, LanguageProvider lang, Roteiro r, int i) {
    final editando = _editandoId == r.id;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: WebColors.surface2,
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
        border: Border.all(color: WebColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(borderRadius: BorderRadius.circular(8), gradient: WebColors.gradient),
                alignment: Alignment.center,
                child: Text('${i + 1}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: editando
                    ? const SizedBox.shrink()
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Flexible(
                                child: Text(r.titulo,
                                    style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w600, fontSize: 15)),
                              ),
                              if (r.origemIa) ...[
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: WebColors.violet.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: WebColors.violet.withValues(alpha: 0.3)),
                                  ),
                                  child: Text(lang.translate('viagem.itinerary.ia.badge'),
                                      style: const TextStyle(color: WebColors.violet, fontSize: 11, fontWeight: FontWeight.w600)),
                                ),
                              ],
                            ],
                          ),
                          if (r.descricao.isNotEmpty) ...[
                            const SizedBox(height: 4),
                            Text(r.descricao, style: const TextStyle(color: WebColors.textMuted, fontSize: 13)),
                          ],
                        ],
                      ),
              ),
              if (widget.isAdmin && !editando)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.edit_outlined, size: 18, color: WebColors.textSecondary),
                      onPressed: () => _iniciarEdicao(r),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, size: 18, color: WebColors.danger),
                      onPressed: () => _deletar(r),
                    ),
                  ],
                ),
            ],
          ),
          if (editando) ...[
            const SizedBox(height: 10),
            _dialogField(_tituloCtrls[r.id]!, lang.translate('itinerary.title')),
            const SizedBox(height: 8),
            _dialogField(_descCtrls[r.id]!, lang.translate('itinerary.description'), maxLines: 3),
            const SizedBox(height: 8),
            Row(
              children: [
                GradientButton(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  onPressed: () => _salvarEdicao(r.id),
                  child: Text(lang.translate('itinerary.save'), style: const TextStyle(fontSize: 13)),
                ),
                const SizedBox(width: 8),
                TextButton(
                  onPressed: () => setState(() => _editandoId = null),
                  style: TextButton.styleFrom(foregroundColor: WebColors.textMuted),
                  child: Text(lang.translate('itinerary.cancel')),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
