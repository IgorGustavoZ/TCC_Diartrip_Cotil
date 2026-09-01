import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import '../../core/app_logger.dart';
import '../../core/web_style.dart';
import '../../models/grupo.dart';
import '../../providers/auth_provider.dart';
import '../../providers/language_provider.dart';
import '../../services/grupo_service.dart';
import '../../services/ia_service.dart';
import '../../widgets/app_drawer.dart';
import '../../widgets/avatar_widget.dart';
import '../../widgets/next_trip_banner.dart';
import '../../widgets/trip_card.dart';

/// Mirrors backend/frontend/lobby.html: dark glass dashboard with a trip
/// grid (next-trip banner + gradient covers) and an AI assistant chat panel.
class LobbyScreen extends StatefulWidget {
  const LobbyScreen({super.key});
  @override
  State<LobbyScreen> createState() => _LobbyScreenState();
}

class _LobbyScreenState extends State<LobbyScreen> {
  List<Grupo> _grupos = [];
  bool _loading = true;

  final List<_Msg> _msgs = [];
  final _chatCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  Grupo? _grupoSelecionado;
  bool _iaLoading = false;

  @override
  void initState() {
    super.initState();
    _loadGrupos();
  }

  @override
  void dispose() {
    _chatCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadGrupos() async {
    try {
      final g = await GrupoService.listar();
      if (mounted) setState(() { _grupos = g; _loading = false; });
    } catch (e, s) {
      AppLogger.captureError('LobbyScreen._loadGrupos', e, s);
      if (mounted) setState(() => _loading = false);
    }
  }

  void _selecionar(Grupo g) {
    // Primeiro toque seleciona a viagem (pro chat de IA); tocar de novo na
    // viagem que já está selecionada abre a página completa da viagem.
    if (_grupoSelecionado?.id == g.id) {
      Navigator.pushNamed(context, '/viagem/${g.id}');
      return;
    }
    setState(() {
      _grupoSelecionado = g;
      _msgs.clear();
    });
  }

  Future<void> _enviarPergunta() async {
    final lang = context.read<LanguageProvider>();
    final texto = _chatCtrl.text.trim();
    if (texto.isEmpty) return;

    if (_grupoSelecionado == null) {
      _chatCtrl.clear();
      setState(() => _msgs.add(_Msg(lang.translate('lobby.chat.selectFirst'), _MsgKind.ai)));
      _scrollDown();
      return;
    }

    if (_iaLoading) return;
    _chatCtrl.clear();
    setState(() {
      _msgs.add(_Msg(texto, _MsgKind.user));
      _iaLoading = true;
    });
    _scrollDown();
    try {
      final resp = await IaService.perguntar(
        pergunta: texto,
        idGrupo: _grupoSelecionado!.id,
      );
      if (mounted) setState(() => _msgs.add(_Msg(resp, _MsgKind.ai)));
    } catch (e) {
      if (mounted) setState(() => _msgs.add(_Msg('${lang.translate('grupos.iaError')} ($e)', _MsgKind.ai)));
    } finally {
      if (mounted) setState(() => _iaLoading = false);
      _scrollDown();
    }
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

  void _showChatBottomSheet(BuildContext context) {
    final lang = context.read<LanguageProvider>();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: WebColors.bg,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(WebColors.radiusLg)),
      ),
      builder: (_) => StatefulBuilder(
        builder: (ctx, setModalState) => SizedBox(
          height: MediaQuery.of(context).size.height * 0.85,
          child: _chatPanel(lang),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().usuario;
    final lang = context.watch<LanguageProvider>();
    final isWide = MediaQuery.of(context).size.width > 800;

    return Scaffold(
      backgroundColor: WebColors.bg,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: const Color(0xB80B1220),
        elevation: 0,
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
            child: const SizedBox.expand(),
          ),
        ),
        title: Text(
          lang.translate('lobby.greeting').replaceFirst('{name}', user?.nome.split(' ').first ?? ''),
          style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 18),
        ),
        iconTheme: const IconThemeData(color: WebColors.textSecondary),
        actions: [
          if (!isWide)
            IconButton(
              icon: const Icon(Icons.smart_toy_outlined, color: WebColors.accent),
              tooltip: lang.translate('lobby.aiAssistant'),
              onPressed: () => _showChatBottomSheet(context),
            ),
          Material(
            color: WebColors.surface2,
            shape: const StadiumBorder(side: BorderSide(color: WebColors.border)),
            child: InkWell(
              customBorder: const StadiumBorder(),
              onTap: () => Navigator.pushNamed(context, '/perfil/${user?.id}'),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(6, 6, 12, 6),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    AvatarWidget(fotoUrl: user?.fotoPerfil, iniciais: user?.iniciais ?? '?', radius: 14),
                    const SizedBox(width: 8),
                    Text(
                      user?.nome.split(' ').first ?? '',
                      style: const TextStyle(color: WebColors.textSecondary, fontSize: 13),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(width: 16),
        ],
      ),
      drawer: AppDrawer(activeRoute: '/lobby'),
      body: Stack(
        children: [
          const Positioned.fill(child: AmbientBackground()),
          SafeArea(
            child: Padding(
              padding: EdgeInsets.only(top: kToolbarHeight + MediaQuery.of(context).padding.top),
              child: isWide
                  ? Row(children: [
                      Expanded(flex: 3, child: _tripsList(lang)),
                      const SizedBox(width: 16),
                      Expanded(flex: 2, child: _chatPanel(lang)),
                    ])
                  : _tripsList(lang),
            ),
          ),
        ],
      ),
      // Atalho rápido pra criar viagem, sempre visível — igual ao botão "+
      // Nova Viagem" do menu lateral, só que sem precisar abrir o drawer.
      floatingActionButton: Tooltip(
        message: lang.translate('lobby.newTrip'),
        child: Material(
          color: WebColors.surface2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(WebColors.radiusMd),
            side: const BorderSide(color: WebColors.border),
          ),
          clipBehavior: Clip.antiAlias,
          elevation: 4,
          child: InkWell(
            onTap: () => Navigator.pushNamed(context, '/nova-viagem'),
            child: const Padding(
              padding: EdgeInsets.all(14),
              child: Icon(Icons.add, color: WebColors.text, size: 24),
            ),
          ),
        ),
      ),
    );
  }

  Widget _tripsList(LanguageProvider lang) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: WebColors.primary));
    }
    if (_grupos.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.luggage_outlined, size: 64, color: WebColors.textMuted),
            const SizedBox(height: 12),
            Text(lang.translate('lobby.noTrips'), style: const TextStyle(color: WebColors.textMuted)),
            const SizedBox(height: 12),
            GradientButton(
              onPressed: () => Navigator.pushNamed(context, '/nova-viagem'),
              child: Text(lang.translate('lobby.createFirst')),
            ),
          ],
        ),
      );
    }

    final proxima = NextTripBanner.proxima(_grupos);

    return RefreshIndicator(
      onRefresh: _loadGrupos,
      color: WebColors.primary,
      backgroundColor: WebColors.bg,
      child: CustomScrollView(
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            sliver: SliverToBoxAdapter(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (proxima != null)
                    NextTripBanner(
                      grupo: proxima,
                      lang: lang,
                      onTap: () => Navigator.pushNamed(context, '/viagem/${proxima.id}'),
                    ),
                  Text(
                    lang.translate('grupos.myTrips'),
                    style: const TextStyle(color: WebColors.text, fontSize: 15, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 12),
                ],
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
            sliver: SliverToBoxAdapter(
              // Wrap em vez de GridView de altura fixa: cada card tem largura
              // fixa mas altura livre, então nome/destino longos ou a barra de
              // orçamento (presente só em alguns cards) nunca ficam espremidos
              // numa célula pequena demais — a causa do "RenderFlex overflowed".
              child: LayoutBuilder(
                builder: (context, constraints) {
                  const spacing = 14.0;
                  const minCardWidth = 260.0;
                  final columns = (constraints.maxWidth / (minCardWidth + spacing)).floor().clamp(1, 6);
                  final cardWidth = (constraints.maxWidth - spacing * (columns - 1)) / columns;
                  return Wrap(
                    spacing: spacing,
                    runSpacing: spacing,
                    children: [
                      for (final g in _grupos)
                        SizedBox(
                          width: cardWidth,
                          child: TripCard(
                            grupo: g,
                            selected: _grupoSelecionado?.id == g.id,
                            onTap: () => _selecionar(g),
                            onLongPress: () => Navigator.pushNamed(context, '/viagem/${g.id}'),
                          ),
                        ),
                    ],
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _chatPanel(LanguageProvider lang) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 16, 16, 16),
      child: GlassContainer(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
              child: Row(
                children: [
                  Text(
                    lang.translate('lobby.aiAssistant'),
                    style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 14),
                  ),
                  const Spacer(),
                  if (_grupoSelecionado != null)
                    Flexible(
                      child: Text(
                        _grupoSelecionado!.nomeGrupo,
                        style: const TextStyle(color: WebColors.textMuted, fontSize: 12),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
              ),
            ),
            Divider(height: 1, color: WebColors.border),
            Expanded(
              child: _msgs.isEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Text(
                          lang.translate('lobby.selectTrip'),
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: WebColors.textMuted, fontSize: 13),
                        ),
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollCtrl,
                      padding: const EdgeInsets.all(18),
                      itemCount: _msgs.length + (_iaLoading ? 1 : 0),
                      itemBuilder: (_, i) {
                        if (i == _msgs.length) {
                          return _ChatLine(
                            label: lang.translate('lobby.chat.aiLabel'),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const SizedBox(
                                  height: 12,
                                  width: 12,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: WebColors.accent),
                                ),
                                const SizedBox(width: 8),
                                Text(lang.translate('lobby.thinking'),
                                    style: const TextStyle(color: WebColors.textMuted, fontSize: 13)),
                              ],
                            ),
                          );
                        }
                        final m = _msgs[i];
                        final isUser = m.kind == _MsgKind.user;
                        return _ChatLine(
                          label: isUser ? lang.translate('lobby.chat.youLabel') : lang.translate('lobby.chat.aiLabel'),
                          child: isUser
                              ? Text(m.text, style: const TextStyle(color: WebColors.textSecondary, fontSize: 14, height: 1.5))
                              : MarkdownBody(
                                  data: m.text,
                                  styleSheet: MarkdownStyleSheet(
                                    p: const TextStyle(color: WebColors.textSecondary, fontSize: 14, height: 1.5),
                                    strong: const TextStyle(color: WebColors.primary, fontWeight: FontWeight.w700),
                                    listBullet: const TextStyle(color: WebColors.textSecondary, fontSize: 14),
                                  ),
                                ),
                        );
                      },
                    ),
            ),
            Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      height: 44,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: WebColors.surface2,
                        borderRadius: BorderRadius.circular(WebColors.radiusPill),
                        border: Border.all(color: WebColors.border),
                      ),
                      child: TextField(
                        controller: _chatCtrl,
                        style: const TextStyle(color: WebColors.text, fontSize: 14),
                        decoration: InputDecoration(
                          filled: false,
                          border: InputBorder.none,
                          enabledBorder: InputBorder.none,
                          focusedBorder: InputBorder.none,
                          isCollapsed: true,
                          hintText: lang.translate('lobby.hint'),
                          hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 14),
                        ),
                        onSubmitted: (_) => _enviarPergunta(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  GradientButton(
                    radius: WebColors.radiusPill,
                    padding: const EdgeInsets.all(12),
                    onPressed: _iaLoading ? null : _enviarPergunta,
                    child: const Icon(Icons.send_rounded, size: 18),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// `<div class="message"><strong>AI:</strong> texto</div>` — plain stacked
/// text, no chat-bubble background, exactly like lobby.html's `#chatMessages`.
class _ChatLine extends StatelessWidget {
  final String label;
  final Widget child;
  const _ChatLine({required this.label, required this.child});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$label:',
            style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 14),
          ),
          const SizedBox(height: 3),
          child,
        ],
      ),
    );
  }
}

enum _MsgKind { user, ai }

class _Msg {
  final String text;
  final _MsgKind kind;
  _Msg(this.text, this.kind);
}
