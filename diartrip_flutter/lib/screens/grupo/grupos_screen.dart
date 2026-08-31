import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import '../../core/api_client.dart';
import '../../core/web_style.dart';
import '../../models/grupo.dart';
import '../../providers/language_provider.dart';
import '../../services/grupo_service.dart';
import '../../services/ia_service.dart';
import '../../widgets/app_drawer.dart';

/// Mirrors backend/frontend/lobby-pags/grupos.html: join-by-code card + a
/// plain list of `.grupo-card` rows (icon, name/destination, "View trip" /
/// "Chat" buttons) — instead of the gradient-cover trip cards used
/// elsewhere. "Chat" now deep-links to the trip's real chat tab
/// (`/viagem/{id}?tab=chat`), matching the site; the AI-only quick chat this
/// screen had before is still reachable via long-press → trip details.
class GruposScreen extends StatefulWidget {
  const GruposScreen({super.key});
  @override
  State<GruposScreen> createState() => _GruposScreenState();
}

class _GruposScreenState extends State<GruposScreen> {
  List<Grupo> _grupos = [];
  List<Grupo>? _resultadoBusca;
  bool _loading = true;
  final _codigoCtrl = TextEditingController();
  final _buscaCtrl = TextEditingController();
  bool _entrando = false;
  bool _buscando = false;
  String? _msg;
  bool _msgErro = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _codigoCtrl.dispose();
    _buscaCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      _grupos = await GrupoService.listar();
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _buscar(String q) async {
    if (q.trim().isEmpty) {
      setState(() => _resultadoBusca = null);
      return;
    }
    setState(() => _buscando = true);
    try {
      final r = await GrupoService.buscar(q.trim());
      if (mounted) setState(() => _resultadoBusca = r);
    } catch (_) {
      if (mounted) setState(() => _resultadoBusca = []);
    } finally {
      if (mounted) setState(() => _buscando = false);
    }
  }

  Future<void> _entrar() async {
    final lang = context.read<LanguageProvider>();
    final codigo = _codigoCtrl.text.trim().toUpperCase();
    if (codigo.length < 4) {
      setState(() { _msg = lang.translate('grupos.enterCodeError'); _msgErro = true; });
      return;
    }
    setState(() { _entrando = true; _msg = null; });
    try {
      await GrupoService.entrar(codigo);
      _codigoCtrl.clear();
      setState(() { _msg = '${lang.translate('grupos.joinSuccess')} ✓'; _msgErro = false; });
      await _load();
    } catch (e) {
      setState(() {
        _msg = e is ApiException ? e.message : lang.translate('grupos.joinError');
        _msgErro = true;
      });
    } finally {
      if (mounted) setState(() => _entrando = false);
    }
  }

  void _abrirTrip(Grupo g) => Navigator.pushNamed(context, '/viagem/${g.id}');
  void _abrirChat(Grupo g) => Navigator.pushNamed(context, '/viagem/${g.id}?tab=chat');

  void _abrirChatIa(Grupo g) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: WebColors.bg,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _IaChatSheet(
        grupo: g,
        onAbrirViagem: () => Navigator.pushNamed(context, '/viagem/${g.id}'),
      ),
    );
  }

  void _abrirInfo(Grupo g) {
    HapticFeedback.mediumImpact();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: WebColors.bg,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _TripInfoSheet(
        grupo: g,
        onAbrirViagem: () => Navigator.pushNamed(context, '/viagem/${g.id}'),
        onAbrirIa: () => _abrirChatIa(g),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    final lista = _resultadoBusca ?? _grupos;
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
        iconTheme: const IconThemeData(color: WebColors.textSecondary),
        title: Text(
          lang.translate('grupos.title'),
          style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 18),
        ),
      ),
      drawer: const AppDrawer(activeRoute: '/grupos'),
      body: Stack(
        children: [
          const Positioned.fill(child: AmbientBackground()),
          SafeArea(
            child: RefreshIndicator(
              onRefresh: _load,
              color: WebColors.primary,
              backgroundColor: WebColors.bg,
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 720),
                  child: ListView(
                    padding: EdgeInsets.fromLTRB(14, kToolbarHeight + 4, 14, 24),
                    children: [
                      _entrarCard(lang),
                      const SizedBox(height: 16),
                      _campoBusca(lang),
                      const SizedBox(height: 20),
                      Text(
                        _resultadoBusca != null ? lang.translate('grupos.searchResults') : lang.translate('grupos.yourGroups'),
                        style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 15),
                      ),
                      if (_resultadoBusca == null) ...[
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            const Icon(Icons.info_outline, size: 12, color: WebColors.textMuted),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(lang.translate('grupos.tapHint'),
                                  style: const TextStyle(color: WebColors.textMuted, fontSize: 11)),
                            ),
                          ],
                        ),
                      ],
                      const SizedBox(height: 14),
                      if (_loading && _resultadoBusca == null)
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 40),
                          child: Center(child: CircularProgressIndicator(color: WebColors.primary)),
                        )
                      else if (lista.isEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 40),
                          child: Center(
                            child: Text(
                              _resultadoBusca != null ? lang.translate('grupos.noGroups') : lang.translate('grupos.empty'),
                              textAlign: TextAlign.center,
                              style: const TextStyle(color: WebColors.textMuted, height: 1.5),
                            ),
                          ),
                        )
                      else
                        for (final g in lista) ...[
                          _GrupoRow(
                            grupo: g,
                            onTap: () => _abrirTrip(g),
                            onChat: () => _abrirChat(g),
                            onLongPress: () => _abrirInfo(g),
                          ),
                          const SizedBox(height: 10),
                        ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _entrarCard(LanguageProvider lang) {
    return GlassContainer(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('🔑 ${lang.translate('grupos.joinTitle')}',
              style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 15)),
          const SizedBox(height: 4),
          Text(lang.translate('grupos.joinDesc'), style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: Container(
                  height: 44,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(
                    color: WebColors.surface2,
                    borderRadius: BorderRadius.circular(WebColors.radiusMd),
                    border: Border.all(color: WebColors.border),
                  ),
                  child: TextField(
                    controller: _codigoCtrl,
                    maxLength: 6,
                    textCapitalization: TextCapitalization.characters,
                    style: const TextStyle(color: WebColors.text, fontSize: 14, letterSpacing: 2),
                    decoration: InputDecoration(
                      filled: false,
                      border: InputBorder.none,
                      enabledBorder: InputBorder.none,
                      focusedBorder: InputBorder.none,
                      isCollapsed: true,
                      counterText: '',
                      hintText: lang.translate('grupos.joinPlaceholder'),
                      hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 13, letterSpacing: 0),
                    ),
                    onSubmitted: (_) => _entrar(),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              GradientButton(
                radius: WebColors.radiusMd,
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                onPressed: _entrando ? null : _entrar,
                child: _entrando
                    ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(lang.translate('grupos.joinBtn'), style: const TextStyle(fontSize: 13)),
              ),
            ],
          ),
          if (_msg != null) ...[
            const SizedBox(height: 10),
            Text(_msg!, style: TextStyle(color: _msgErro ? WebColors.danger : WebColors.success, fontSize: 12)),
          ],
        ],
      ),
    );
  }

  Widget _campoBusca(LanguageProvider lang) {
    return Container(
      height: 44,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: WebColors.surface,
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
        border: Border.all(color: WebColors.border),
      ),
      child: Row(
        children: [
          const Icon(Icons.search, size: 18, color: WebColors.textMuted),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              controller: _buscaCtrl,
              style: const TextStyle(color: WebColors.text, fontSize: 14),
              decoration: InputDecoration(
                filled: false,
                border: InputBorder.none,
                enabledBorder: InputBorder.none,
                focusedBorder: InputBorder.none,
                isCollapsed: true,
                hintText: lang.translate('grupos.search'),
                hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 14),
              ),
              onChanged: _buscar,
            ),
          ),
          if (_buscando)
            const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2, color: WebColors.accent))
          else if (_buscaCtrl.text.isNotEmpty)
            InkWell(
              onTap: () {
                _buscaCtrl.clear();
                setState(() => _resultadoBusca = null);
              },
              child: const Icon(Icons.close, size: 18, color: WebColors.textMuted),
            ),
        ],
      ),
    );
  }
}

class _GrupoRow extends StatelessWidget {
  final Grupo grupo;
  final VoidCallback onTap;
  final VoidCallback onChat;
  final VoidCallback onLongPress;

  const _GrupoRow({required this.grupo, required this.onTap, required this.onChat, required this.onLongPress});

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return GlassContainer(
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          onLongPress: onLongPress,
          borderRadius: BorderRadius.circular(WebColors.radiusLg),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(WebColors.radiusMd),
                    gradient: WebColors.gradient,
                  ),
                  alignment: Alignment.center,
                  child: const Icon(Icons.flight_takeoff, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        grupo.nomeGrupo,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w600, fontSize: 15),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '📍 ${grupo.destinoPrincipal}${grupo.dataInicio != null ? ' · ${grupo.dataInicio}' : ''}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: WebColors.textMuted, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    _acaoBtn(lang.translate('grupos.viewTrip'), onTap),
                    const SizedBox(height: 6),
                    _acaoBtn(lang.translate('grupos.chat'), onChat, gradient: true),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _acaoBtn(String label, VoidCallback onTap, {bool gradient = false}) {
    if (gradient) {
      return GradientButton(
        radius: WebColors.radiusSm,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        onPressed: onTap,
        child: Text(label, style: const TextStyle(fontSize: 11)),
      );
    }
    return Material(
      color: WebColors.surface2,
      borderRadius: BorderRadius.circular(WebColors.radiusSm),
      child: InkWell(
        borderRadius: BorderRadius.circular(WebColors.radiusSm),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          child: Text(label, style: const TextStyle(color: WebColors.textSecondary, fontSize: 11, fontWeight: FontWeight.w600)),
        ),
      ),
    );
  }
}

typedef _Msg = ({String texto, bool isUser, bool isError});

class _IaChatSheet extends StatefulWidget {
  final Grupo grupo;
  final VoidCallback onAbrirViagem;

  const _IaChatSheet({required this.grupo, required this.onAbrirViagem});

  @override
  State<_IaChatSheet> createState() => _IaChatSheetState();
}

class _IaChatSheetState extends State<_IaChatSheet> {
  final _ctrl = TextEditingController();
  final _scroll = ScrollController();
  final List<_Msg> _msgs = [];
  bool _loading = false;

  List<String> _sugestoes(LanguageProvider lang) => [
    lang.translate('grupos.suggest1'),
    lang.translate('grupos.suggest2'),
    lang.translate('grupos.suggest3'),
    lang.translate('grupos.suggest4'),
  ];

  @override
  void dispose() {
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _enviar([String? texto]) async {
    final pergunta = (texto ?? _ctrl.text).trim();
    if (pergunta.isEmpty || _loading) return;
    _ctrl.clear();
    setState(() {
      _msgs.add((texto: pergunta, isUser: true, isError: false));
      _loading = true;
    });
    _scrollBottom();
    try {
      final resp = await IaService.perguntar(
        pergunta: pergunta,
        idGrupo: widget.grupo.id,
      );
      if (mounted) {
        setState(() => _msgs.add((texto: resp, isUser: false, isError: false)));
        _scrollBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _msgs.add((
          texto: context.read<LanguageProvider>().translate('grupos.iaError'),
          isUser: false,
          isError: true,
        )));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _scrollBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    final height = MediaQuery.of(context).size.height * 0.88;

    return SizedBox(
      height: height,
      child: Column(
        children: [
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 6),
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: WebColors.textMuted.withValues(alpha: 0.35),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 8, 10),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(9),
                  decoration: BoxDecoration(
                    color: WebColors.primary.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.auto_awesome, color: WebColors.primary, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(lang.translate('lobby.aiAssistant'),
                          style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 14)),
                      Text(widget.grupo.nomeGrupo,
                          style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.open_in_new, size: 20, color: WebColors.textMuted),
                  tooltip: lang.translate('grupos.openTripFull'),
                  onPressed: () {
                    Navigator.pop(context);
                    widget.onAbrirViagem();
                  },
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20, color: WebColors.textMuted),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),
          Divider(height: 1, color: WebColors.border),
          Expanded(
            child: _msgs.isEmpty ? _emptyState(lang) : _messageList(),
          ),
          if (_loading)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: WebColors.surface2,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _Dot(delay: 0),
                        SizedBox(width: 4),
                        _Dot(delay: 150),
                        SizedBox(width: 4),
                        _Dot(delay: 300),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          Padding(
            padding: EdgeInsets.fromLTRB(12, 8, 12, bottom + 12),
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
                      controller: _ctrl,
                      style: const TextStyle(color: WebColors.text, fontSize: 14),
                      decoration: InputDecoration(
                        filled: false,
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        isCollapsed: true,
                        hintText: lang.translate('grupos.iaHint'),
                        hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 14),
                      ),
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _enviar(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                GradientButton(
                  radius: WebColors.radiusPill,
                  padding: const EdgeInsets.all(12),
                  onPressed: _loading ? null : () => _enviar(),
                  child: const Icon(Icons.send_rounded, size: 20),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _emptyState(LanguageProvider lang) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: WebColors.primary.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.travel_explore, size: 40, color: WebColors.primary),
          ),
          const SizedBox(height: 16),
          Text(
            widget.grupo.destinoPrincipal,
            style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 16),
          ),
          const SizedBox(height: 6),
          Text(
            lang.translate('grupos.iaEmptyHint'),
            textAlign: TextAlign.center,
            style: const TextStyle(color: WebColors.textMuted, fontSize: 13),
          ),
          const SizedBox(height: 24),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: _sugestoes(lang)
                .map((s) => ActionChip(
                      label: Text(s, style: const TextStyle(color: WebColors.text, fontSize: 12)),
                      onPressed: () => _enviar(s),
                      backgroundColor: WebColors.surface2,
                      side: BorderSide(color: WebColors.primary.withValues(alpha: 0.3)),
                    ))
                .toList(),
          ),
        ],
      ),
    );
  }

  Widget _messageList() {
    return ListView.builder(
      controller: _scroll,
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
      itemCount: _msgs.length,
      itemBuilder: (_, i) {
        final m = _msgs[i];
        if (m.isUser) {
          return Align(
            alignment: Alignment.centerRight,
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 4),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.78,
              ),
              decoration: BoxDecoration(
                gradient: WebColors.gradient,
                borderRadius: BorderRadius.circular(16).copyWith(
                  bottomRight: const Radius.circular(4),
                ),
              ),
              child: Text(m.texto,
                  style: const TextStyle(color: Colors.white, fontSize: 14)),
            ),
          );
        }
        return Align(
          alignment: Alignment.centerLeft,
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 4),
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.88,
            ),
            decoration: BoxDecoration(
              color: m.isError
                  ? WebColors.danger.withValues(alpha: 0.15)
                  : WebColors.surface2,
              borderRadius: BorderRadius.circular(16).copyWith(
                bottomLeft: const Radius.circular(4),
              ),
            ),
            child: m.isError
                ? Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline, size: 16, color: WebColors.danger),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(m.texto,
                            style: const TextStyle(color: WebColors.danger, fontSize: 13)),
                      ),
                    ],
                  )
                : MarkdownBody(
                    data: m.texto,
                    styleSheet: MarkdownStyleSheet(
                      p: const TextStyle(color: WebColors.text, fontSize: 14, height: 1.4),
                      strong: const TextStyle(
                          color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 14),
                      em: const TextStyle(color: WebColors.text, fontStyle: FontStyle.italic, fontSize: 14),
                      listBullet: const TextStyle(color: WebColors.text, fontSize: 14),
                      code: const TextStyle(
                          color: WebColors.accent, fontSize: 13, fontFamily: 'monospace'),
                      blockquoteDecoration: BoxDecoration(
                        border: Border(
                          left: BorderSide(
                              color: WebColors.primary.withValues(alpha: 0.6), width: 3),
                        ),
                      ),
                    ),
                  ),
          ),
        );
      },
    );
  }
}

class _Dot extends StatefulWidget {
  final int delay;
  const _Dot({required this.delay});
  @override
  State<_Dot> createState() => _DotState();
}

class _DotState extends State<_Dot> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _anim = Tween<double>(begin: 0.3, end: 1).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
    Future.delayed(Duration(milliseconds: widget.delay), () {
      if (mounted) _ctrl.repeat(reverse: true);
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _anim,
      child: Container(
        width: 7,
        height: 7,
        decoration: const BoxDecoration(
          color: WebColors.textMuted,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}

class _TripInfoSheet extends StatelessWidget {
  final Grupo grupo;
  final VoidCallback onAbrirViagem;
  final VoidCallback onAbrirIa;

  const _TripInfoSheet({
    required this.grupo,
    required this.onAbrirViagem,
    required this.onAbrirIa,
  });

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(
          20, 0, 20, MediaQuery.of(context).viewInsets.bottom + 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 16),
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: WebColors.textMuted.withValues(alpha: 0.35),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  gradient: WebColors.gradient,
                ),
                child: const Icon(Icons.flight_takeoff, color: Colors.white, size: 26),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(grupo.nomeGrupo,
                        style: const TextStyle(
                            color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 17)),
                    Text(grupo.destinoPrincipal,
                        style: const TextStyle(
                            color: WebColors.textMuted, fontSize: 13)),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close, color: WebColors.textSecondary),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Divider(height: 1, color: WebColors.border),
          const SizedBox(height: 16),
          if (grupo.dataInicio != null)
            _infoRow(
              Icons.calendar_today_outlined,
              lang.translate('grupos.period'),
              '${grupo.dataInicio} → ${grupo.dataFim ?? lang.translate('grupos.tbd')}',
            ),
          if (grupo.orcamento != null)
            _infoRow(
              Icons.attach_money,
              lang.translate('grupos.budgetLabel'),
              'R\$ ${grupo.orcamento!.toStringAsFixed(2)}',
            ),
          if (grupo.tipoViagem != null)
            _infoRow(Icons.category_outlined, lang.translate('grupos.type'), grupo.tipoViagem!),
          if (grupo.preferencias != null && grupo.preferencias!.isNotEmpty)
            _infoRow(Icons.favorite_outline, lang.translate('grupos.preferencesLabel'), grupo.preferencias!),
          if (grupo.codigoConvite != null) ...[
            const SizedBox(height: 8),
            Text(lang.translate('grupos.inviteCode'),
                style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
            const SizedBox(height: 6),
            GestureDetector(
              onTap: () {
                Clipboard.setData(ClipboardData(text: grupo.codigoConvite!));
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(lang.translate('grupos.codeCopied'))),
                );
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: WebColors.surface2,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                      color: WebColors.primary.withValues(alpha: 0.3)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      grupo.codigoConvite!,
                      style: const TextStyle(
                        color: WebColors.text,
                        fontFamily: 'monospace',
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 4,
                      ),
                    ),
                    const Icon(Icons.copy, color: WebColors.primary, size: 18),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.auto_awesome, size: 16),
                  label: Text(lang.translate('grupos.chatIA')),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: WebColors.textSecondary,
                    side: const BorderSide(color: WebColors.borderStrong),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(WebColors.radiusMd)),
                  ),
                  onPressed: () {
                    Navigator.pop(context);
                    onAbrirIa();
                  },
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: GradientButton(
                  onPressed: () {
                    Navigator.pop(context);
                    onAbrirViagem();
                  },
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.open_in_new, size: 16),
                      const SizedBox(width: 8),
                      Text(lang.translate('grupos.openTrip')),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 18, color: WebColors.textMuted),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        color: WebColors.textMuted, fontSize: 11)),
                Text(value,
                    style: const TextStyle(color: WebColors.text, fontSize: 14)),
              ],
            ),
          ],
        ),
      );
}
