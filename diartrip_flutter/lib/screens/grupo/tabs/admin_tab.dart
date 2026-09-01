import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/api_client.dart';
import '../../../core/app_logger.dart';
import '../../../core/web_style.dart';
import '../../../models/dashboard.dart';
import '../../../models/grupo.dart';
import '../../../models/solicitacao.dart';
import '../../../providers/language_provider.dart';
import '../../../services/grupo_service.dart';
import '../../../services/solicitacao_service.dart';
import '../../../widgets/avatar_widget.dart';
import '../../../widgets/confirm_dialog.dart';

/// Aba "admin" de viagem.html: estatísticas + ranking, gerenciar membros,
/// publicar/despublicar em Explorar Viagens, e solicitações de participação.
/// Só aparece (no shell) quando o usuário é admin do grupo. O dashboard vem
/// pronto do [ViagemScreen] (compartilhado com Visão Geral/Minhas Finanças);
/// só as solicitações são buscadas aqui, por serem exclusivas desta aba.
class AdminTab extends StatefulWidget {
  final int idGrupo;
  final Grupo grupo;
  final DashboardCompleto? dash;
  final List<Membro> membros;
  final int meId;
  final bool isAdmin;
  final Future<void> Function() onReload;

  const AdminTab({
    super.key,
    required this.idGrupo,
    required this.grupo,
    required this.dash,
    required this.membros,
    required this.meId,
    required this.isAdmin,
    required this.onReload,
  });

  @override
  State<AdminTab> createState() => _AdminTabState();
}

class _AdminTabState extends State<AdminTab> {
  List<Solicitacao> _solicitacoes = [];
  bool _loadingSolicitacoes = true;
  final _limiteCtrl = TextEditingController();
  bool _publicando = false;
  String? _erroExplorar;

  @override
  void initState() {
    super.initState();
    if (widget.isAdmin) {
      _loadSolicitacoes();
      _limiteCtrl.text = (widget.grupo.limiteParticipantes ?? '').toString();
    }
  }

  @override
  void didUpdateWidget(covariant AdminTab old) {
    super.didUpdateWidget(old);
    if (!old.grupo.publica && !_publicando && _limiteCtrl.text.isEmpty) {
      _limiteCtrl.text = (widget.grupo.limiteParticipantes ?? '').toString();
    }
  }

  @override
  void dispose() {
    _limiteCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadSolicitacoes() async {
    setState(() => _loadingSolicitacoes = true);
    try {
      final s = await SolicitacaoService.listar(widget.idGrupo);
      if (mounted) setState(() => _solicitacoes = s);
    } catch (e, s) {
      AppLogger.captureError('AdminTab._loadSolicitacoes', e, s);
    } finally {
      if (mounted) setState(() => _loadingSolicitacoes = false);
    }
  }

  Future<void> _publicar() async {
    final lang = context.read<LanguageProvider>();
    final limite = int.tryParse(_limiteCtrl.text);
    if (limite == null || limite < 1) {
      setState(() => _erroExplorar = lang.translate('viagem.explore.limitError'));
      return;
    }
    setState(() {
      _publicando = true;
      _erroExplorar = null;
    });
    try {
      await GrupoService.publicar(widget.idGrupo, publica: true, limiteParticipantes: limite);
      widget.onReload();
    } catch (e) {
      setState(() => _erroExplorar = e is ApiException ? e.message : lang.translate('viagem.explore.errorPublish'));
    } finally {
      if (mounted) setState(() => _publicando = false);
    }
  }

  Future<void> _despublicar() async {
    final lang = context.read<LanguageProvider>();
    final ok = await confirmarAcao(
      context,
      titulo: lang.translate('viagem.explore.confirmUnpublish'),
      mensagem: lang.translate('viagem.explore.confirmUnpublishBody'),
      textoConfirmar: lang.translate('viagem.explore.unpublish'),
    );
    if (!ok) return;
    try {
      await GrupoService.publicar(widget.idGrupo, publica: false);
      widget.onReload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e is ApiException ? e.message : lang.translate('viagem.explore.errorUnpublish'))),
        );
      }
    }
  }

  Future<void> _responder(Solicitacao s, bool aceitar) async {
    final lang = context.read<LanguageProvider>();
    try {
      if (aceitar) {
        await SolicitacaoService.aceitar(s.id);
      } else {
        await SolicitacaoService.recusar(s.id);
      }
      _loadSolicitacoes();
      if (aceitar) widget.onReload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e is ApiException ? e.message : lang.translate('viagem.explore.errorRespond'))),
        );
      }
    }
  }

  Future<void> _promover(Membro m) async {
    final lang = context.read<LanguageProvider>();
    final ok = await confirmarAcao(
      context,
      titulo: lang.translate('viagem.confirmPromote'),
      mensagem: lang.translate('viagem.confirmPromoteBody'),
      textoConfirmar: lang.translate('viagem.action.promote'),
      perigo: false,
    );
    if (!ok) return;
    try {
      await GrupoService.promover(widget.idGrupo, m.id);
      widget.onReload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e is ApiException ? e.message : lang.translate('viagem.errorPromote'))),
        );
      }
    }
  }

  Future<void> _rebaixar(Membro m) async {
    final lang = context.read<LanguageProvider>();
    final ok = await confirmarAcao(
      context,
      titulo: lang.translate('viagem.confirmDemote'),
      mensagem: lang.translate('viagem.confirmDemoteBody'),
      textoConfirmar: lang.translate('viagem.action.demote'),
    );
    if (!ok) return;
    try {
      await GrupoService.rebaixar(widget.idGrupo, m.id);
      widget.onReload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e is ApiException ? e.message : lang.translate('viagem.errorDemote'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();

    if (!widget.isAdmin) {
      return Center(
        child: Text(lang.translate('admin.required'), style: const TextStyle(color: WebColors.textMuted)),
      );
    }
    final adminData = widget.dash?.admin;
    return RefreshIndicator(
      onRefresh: () async {
        await Future.wait([widget.onReload(), _loadSolicitacoes()]);
      },
      color: WebColors.primary,
      backgroundColor: WebColors.bg,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 0, 14, 24),
        children: [
          TripCardExpanded(
            title: '👑 ${lang.translate('admin.panel')}',
            child: adminData == null
                ? const Center(
                    child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator(color: WebColors.primary)),
                  )
                : Wrap(
                    spacing: 16,
                    runSpacing: 16,
                    children: [
                      SizedBox(
                        width: _cardWidth(context),
                        child: DashboardCard(
                          title: '🔥 ${lang.translate('admin.ranking')}',
                          child: Column(
                            children: List.generate(adminData.ranking.length, (i) {
                              final r = adminData.ranking[i];
                              const medals = ['🥇', '🥈', '🥉'];
                              final prefix = i < medals.length ? medals[i] : '${i + 1}.';
                              return CategoryItemRow(
                                left: Text('$prefix ${r.nome}', style: const TextStyle(color: WebColors.text, fontSize: 14)),
                                right: Text('R\$ ${r.total.toStringAsFixed(2)}',
                                    style: const TextStyle(color: WebColors.primary, fontWeight: FontWeight.w700, fontSize: 14)),
                              );
                            }),
                          ),
                        ),
                      ),
                      SizedBox(
                        width: _cardWidth(context),
                        child: DashboardCard(
                          title: '📈 ${lang.translate('admin.statistics')}',
                          child: Column(
                            children: [
                              StatRow(label: lang.translate('admin.activeMembers'), value: '${adminData.estatisticas.membrosAtivos}'),
                              StatRow(label: lang.translate('admin.itineraryItems'), value: '${adminData.estatisticas.itensNoRoteiro}'),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
          ),
          TripCardExpanded(
            title: lang.translate('admin.manageMembers'),
            child: Column(
              children: widget.membros.map((m) => _membroRow(context, lang, m)).toList(),
            ),
          ),
          TripCardExpanded(
            title: lang.translate('viagem.explore.panel'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.grupo.publica
                      ? '${lang.translate('viagem.explore.published')} (${widget.grupo.vagasOcupadas}/${widget.grupo.limiteParticipantes ?? '—'})'
                      : lang.translate('viagem.explore.notPublished'),
                  style: const TextStyle(color: WebColors.textMuted, fontSize: 14),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: 160,
                  child: TextField(
                    controller: _limiteCtrl,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(color: WebColors.text, fontSize: 14),
                    decoration: InputDecoration(
                      labelText: lang.translate('viagem.explore.limitLabel'),
                      labelStyle: const TextStyle(color: WebColors.textMuted, fontSize: 12),
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
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    GradientButton(
                      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                      onPressed: _publicando ? null : _publicar,
                      child: _publicando
                          ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : Text(
                              widget.grupo.publica ? '🔄 ${lang.translate('viagem.explore.update')}' : lang.translate('viagem.explore.publish'),
                              style: const TextStyle(fontSize: 13)),
                    ),
                    if (widget.grupo.publica) ...[
                      const SizedBox(width: 10),
                      OutlinedButton(
                        onPressed: _despublicar,
                        style: OutlinedButton.styleFrom(
                          foregroundColor: WebColors.danger,
                          side: BorderSide(color: WebColors.danger.withValues(alpha: 0.35)),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        ),
                        child: Text(lang.translate('viagem.explore.unpublish'), style: const TextStyle(fontSize: 13)),
                      ),
                    ],
                  ],
                ),
                if (_erroExplorar != null) ...[
                  const SizedBox(height: 8),
                  Text(_erroExplorar!, style: const TextStyle(color: WebColors.danger, fontSize: 12)),
                ],
              ],
            ),
          ),
          TripCardExpanded(
            title: lang.translate('viagem.explore.requests'),
            child: _loadingSolicitacoes
                ? const Center(child: Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator(color: WebColors.primary)))
                : _solicitacoes.isEmpty
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: Text(lang.translate('viagem.explore.noRequests'),
                              style: const TextStyle(color: WebColors.textMuted, fontSize: 14)),
                        ),
                      )
                    : Column(children: _solicitacoes.map((s) => _solicitacaoRow(context, lang, s)).toList()),
          ),
        ],
      ),
    );
  }

  Widget _membroRow(BuildContext context, LanguageProvider lang, Membro m) {
    final isMe = m.id == widget.meId;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: WebColors.surface2,
          borderRadius: BorderRadius.circular(WebColors.radiusMd),
          border: Border.all(color: WebColors.border),
        ),
        child: Row(
          children: [
            AvatarWidget(fotoUrl: m.fotoPerfil, iniciais: m.nome.isNotEmpty ? m.nome[0].toUpperCase() : '?', radius: 18),
            const SizedBox(width: 12),
            Expanded(
              child: Row(
                children: [
                  Flexible(
                    child: Text(m.nome,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w600, fontSize: 14)),
                  ),
                  if (isMe) ...[
                    const SizedBox(width: 6),
                    Text(lang.translate('admin.you2'), style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
                  ],
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: (m.isAdmin ? WebColors.warning : WebColors.textSecondary).withValues(alpha: 0.14),
                borderRadius: BorderRadius.circular(WebColors.radiusPill),
              ),
              child: Text(
                m.isAdmin ? lang.translate('viagem.badge.admin') : lang.translate('viagem.badge.member'),
                style: TextStyle(
                  color: m.isAdmin ? WebColors.warning : WebColors.textSecondary,
                  fontWeight: FontWeight.w600,
                  fontSize: 11,
                ),
              ),
            ),
            if (!isMe) ...[
              const SizedBox(width: 6),
              PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert, size: 18, color: WebColors.textMuted),
                color: WebColors.bg2,
                itemBuilder: (_) => [
                  if (!m.isAdmin)
                    PopupMenuItem(
                      value: 'promover',
                      child: Text(lang.translate('viagem.action.promote'), style: const TextStyle(color: WebColors.text)),
                    ),
                  if (m.isAdmin)
                    PopupMenuItem(
                      value: 'rebaixar',
                      child: Text(lang.translate('viagem.action.demote'), style: const TextStyle(color: WebColors.text)),
                    ),
                ],
                onSelected: (v) {
                  if (v == 'promover') _promover(m);
                  if (v == 'rebaixar') _rebaixar(m);
                },
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _solicitacaoRow(BuildContext context, LanguageProvider lang, Solicitacao s) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: WebColors.surface2,
          borderRadius: BorderRadius.circular(WebColors.radiusMd),
          border: Border.all(color: WebColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                AvatarWidget(fotoUrl: s.fotoPerfil, iniciais: s.nome.isNotEmpty ? s.nome[0].toUpperCase() : '?', radius: 18),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(s.nome,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w600, fontSize: 14)),
                ),
              ],
            ),
            if (s.mensagem != null && s.mensagem!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(s.mensagem!, style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
            ],
            if (s.orcamento != null) ...[
              const SizedBox(height: 6),
              Text('💰 R\$ ${s.orcamento!.toStringAsFixed(2)}', style: const TextStyle(color: WebColors.textSecondary, fontSize: 12)),
            ],
            const SizedBox(height: 10),
            Row(
              children: [
                GradientButton(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  onPressed: () => _responder(s, true),
                  child: Text(lang.translate('viagem.explore.accept'), style: const TextStyle(fontSize: 12)),
                ),
                const SizedBox(width: 8),
                OutlinedButton(
                  onPressed: () => _responder(s, false),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: WebColors.danger,
                    side: BorderSide(color: WebColors.danger.withValues(alpha: 0.35)),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  ),
                  child: Text(lang.translate('viagem.explore.reject'), style: const TextStyle(fontSize: 12)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  double _cardWidth(BuildContext context) {
    final w = MediaQuery.of(context).size.width - 28 - 40 - 16;
    return w < 260 ? w : (w > 560 ? (w - 16) / 2 : w);
  }
}
