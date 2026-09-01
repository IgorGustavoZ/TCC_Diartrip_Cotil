import 'dart:typed_data';
import 'dart:ui';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/web_style.dart';
import '../../models/comentario.dart';
import '../../models/post.dart';
import '../../providers/auth_provider.dart';
import '../../providers/language_provider.dart';
import '../../services/post_service.dart';
import '../../services/social_service.dart';
import '../../widgets/app_drawer.dart';
import '../../widgets/avatar_widget.dart';

/// Mirrors backend/frontend/lobby-pags/feed.html: compose box always
/// visible at the top (not behind a toggle), posts as discrete glass cards
/// (header → text → image → pill actions with inline counts → comments),
/// same order the site uses — instead of the Instagram-style layout this
/// screen had before.
class FeedScreen extends StatefulWidget {
  const FeedScreen({super.key});
  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  List<Post> _posts = [];
  bool _loading = true;
  String? _erro;
  final _conteudoCtrl = TextEditingController();
  final _composeFocus = FocusNode();
  final _scrollCtrl = ScrollController();
  XFile? _imagem;
  Uint8List? _imagemBytes;
  bool _publishing = false;
  bool _showComposeFab = false;

  @override
  void initState() {
    super.initState();
    _load();
    _scrollCtrl.addListener(_onScroll);
  }

  @override
  void dispose() {
    _conteudoCtrl.dispose();
    _composeFocus.dispose();
    _scrollCtrl.removeListener(_onScroll);
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    final show = _scrollCtrl.offset > 200;
    if (show != _showComposeFab) setState(() => _showComposeFab = show);
  }

  Future<void> _irParaCompor() async {
    await _scrollCtrl.animateTo(0, duration: const Duration(milliseconds: 350), curve: Curves.easeOut);
    if (mounted) _composeFocus.requestFocus();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _erro = null; });
    try {
      final p = await PostService.listarTodos();
      if (mounted) setState(() { _posts = p; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _loading = false; _erro = e.toString(); });
    }
  }

  Future<void> _pickImage() async {
    final f = await ImagePicker()
        .pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (f != null) {
      final bytes = await f.readAsBytes();
      setState(() {
        _imagem = f;
        _imagemBytes = bytes;
      });
    }
  }

  Future<void> _publish() async {
    final texto = _conteudoCtrl.text.trim();
    if (texto.isEmpty && _imagemBytes == null) return;
    setState(() => _publishing = true);
    try {
      await PostService.criar(
        conteudo: texto,
        imagemBytes: _imagemBytes,
        imagemFilename: _imagem?.name,
        imagemMime: _imagem?.mimeType,
      );
      _conteudoCtrl.clear();
      setState(() { _imagem = null; _imagemBytes = null; });
      await _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _publishing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final me = context.watch<AuthProvider>().usuario;
    final lang = context.watch<LanguageProvider>();
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
          lang.translate('feed.header'),
          style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 18),
        ),
        actions: [
          Material(
            color: WebColors.surface2,
            shape: const CircleBorder(side: BorderSide(color: WebColors.border)),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: () => Navigator.pushNamed(context, '/perfil/${me?.id}'),
              child: Padding(
                padding: const EdgeInsets.all(3),
                child: AvatarWidget(fotoUrl: me?.fotoPerfil, iniciais: me?.iniciais ?? '?', radius: 16),
              ),
            ),
          ),
          const SizedBox(width: 16),
        ],
      ),
      drawer: const AppDrawer(activeRoute: '/feed'),
      body: Stack(
        children: [
          const Positioned.fill(child: AmbientBackground()),
          SafeArea(
            child: RefreshIndicator(
              onRefresh: _load,
              color: WebColors.primary,
              backgroundColor: WebColors.bg,
              child: _loading
                  ? const Center(child: CircularProgressIndicator(color: WebColors.primary))
                  : _erro != null
                      ? ListView(
                          padding: EdgeInsets.only(top: kToolbarHeight + 4),
                          children: [
                            Center(
                              child: Column(
                                children: [
                                  const Icon(Icons.wifi_off, size: 48, color: WebColors.textMuted),
                                  const SizedBox(height: 12),
                                  Text(lang.translate('feed.loadError'), style: const TextStyle(color: WebColors.textMuted)),
                                  const SizedBox(height: 12),
                                  TextButton(onPressed: _load, child: Text(lang.translate('feed.retry'))),
                                ],
                              ),
                            ),
                          ],
                        )
                      : Center(
                          child: ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 600),
                            child: ListView(
                              controller: _scrollCtrl,
                              padding: EdgeInsets.fromLTRB(14, kToolbarHeight + 4, 14, 24),
                              children: [
                                _CreateCard(
                                  me: me,
                                  ctrl: _conteudoCtrl,
                                  focusNode: _composeFocus,
                                  imagemBytes: _imagemBytes,
                                  publishing: _publishing,
                                  onPickImage: _pickImage,
                                  onRemoveImage: () => setState(() {
                                    _imagem = null;
                                    _imagemBytes = null;
                                  }),
                                  onPublish: _publish,
                                ),
                                const SizedBox(height: 16),
                                if (_posts.isEmpty)
                                  Padding(
                                    padding: const EdgeInsets.symmetric(vertical: 48),
                                    child: Center(
                                      child: Text(lang.translate('feed.empty'), style: const TextStyle(color: WebColors.textMuted)),
                                    ),
                                  )
                                else
                                  for (final p in _posts) ...[
                                    _PostCard(key: ValueKey(p.id), post: p, meId: me?.id ?? 0, onDeleted: _load),
                                    const SizedBox(height: 16),
                                  ],
                              ],
                            ),
                          ),
                        ),
            ),
          ),
        ],
      ),
      // Só aparece depois de rolar a lista — perto do topo o cartão de criar
      // post já está visível, então o botão seria redundante ali.
      floatingActionButton: _showComposeFab
          ? Material(
              color: WebColors.surface2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(WebColors.radiusMd),
                side: const BorderSide(color: WebColors.border),
              ),
              clipBehavior: Clip.antiAlias,
              elevation: 4,
              child: InkWell(
                onTap: _irParaCompor,
                child: const Padding(
                  padding: EdgeInsets.all(14),
                  child: Icon(Icons.edit_outlined, color: WebColors.text, size: 22),
                ),
              ),
            )
          : null,
    );
  }
}

class _CreateCard extends StatelessWidget {
  final dynamic me;
  final TextEditingController ctrl;
  final FocusNode? focusNode;
  final Uint8List? imagemBytes;
  final bool publishing;
  final VoidCallback onPickImage;
  final VoidCallback onRemoveImage;
  final VoidCallback onPublish;

  const _CreateCard({
    required this.me,
    required this.ctrl,
    this.focusNode,
    required this.imagemBytes,
    required this.publishing,
    required this.onPickImage,
    required this.onRemoveImage,
    required this.onPublish,
  });

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return GlassContainer(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AvatarWidget(fotoUrl: me?.fotoPerfil, iniciais: me?.iniciais ?? '?', radius: 18),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: ctrl,
                  focusNode: focusNode,
                  maxLines: 3,
                  style: const TextStyle(color: WebColors.text),
                  decoration: InputDecoration(
                    hintText: lang.translate('feed.placeholder'),
                    hintStyle: const TextStyle(color: WebColors.textMuted),
                    filled: true,
                    fillColor: WebColors.surface2,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(WebColors.radiusMd), borderSide: BorderSide.none),
                  ),
                ),
              ),
            ],
          ),
          if (imagemBytes != null) ...[
            const SizedBox(height: 8),
            Stack(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(WebColors.radiusMd),
                  child: Image.memory(imagemBytes!, height: 160, width: double.infinity, fit: BoxFit.cover),
                ),
                Positioned(
                  top: 6,
                  right: 6,
                  child: GestureDetector(
                    onTap: onRemoveImage,
                    child: Container(
                      width: 28,
                      height: 28,
                      decoration: BoxDecoration(color: WebColors.bg.withValues(alpha: 0.6), shape: BoxShape.circle),
                      child: const Icon(Icons.close, color: Colors.white, size: 16),
                    ),
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              OutlinedButton.icon(
                onPressed: onPickImage,
                icon: const Icon(Icons.photo_outlined, size: 16, color: WebColors.textSecondary),
                label: Text(lang.translate('feed.photo'), style: const TextStyle(color: WebColors.textSecondary, fontSize: 13)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: WebColors.border),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(WebColors.radiusSm)),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                ),
              ),
              const Spacer(),
              GradientButton(
                radius: WebColors.radiusSm,
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                onPressed: publishing ? null : onPublish,
                child: publishing
                    ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(lang.translate('feed.publish'), style: const TextStyle(fontSize: 13)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _PostCard extends StatefulWidget {
  final Post post;
  final int meId;
  final VoidCallback onDeleted;

  const _PostCard({
    super.key,
    required this.post,
    required this.meId,
    required this.onDeleted,
  });

  @override
  State<_PostCard> createState() => _PostCardState();
}

class _PostCardState extends State<_PostCard> {
  late bool _jaCurtiu;
  late int _curtidas;
  late List<Comentario> _comentarios;
  bool _showComments = false;
  bool _savingLike = false;
  bool _commenting = false;
  bool _heartBig = false;
  final _comentCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _jaCurtiu = widget.post.jaCurtiu;
    _curtidas = widget.post.curtidas;
    _comentarios = List<Comentario>.from(widget.post.comentarios);
  }

  @override
  void dispose() {
    _comentCtrl.dispose();
    super.dispose();
  }

  Future<void> _curtir() async {
    if (_savingLike) return;
    setState(() => _savingLike = true);
    try {
      final res = await SocialService.curtirPost(widget.post.id);
      if (!mounted) return;
      setState(() {
        _jaCurtiu = res['curtiu'] as bool;
        _curtidas = res['total_curtidas'] as int;
        if (_jaCurtiu) _heartBig = true;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _savingLike = false);
    }
  }

  Future<void> _enviarComentario() async {
    final texto = _comentCtrl.text.trim();
    if (texto.isEmpty) return;
    setState(() => _commenting = true);
    try {
      final c = await SocialService.comentarPost(widget.post.id, texto);
      _comentCtrl.clear();
      if (mounted) setState(() => _comentarios.add(c));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _commenting = false);
    }
  }

  void _confirmDelete() async {
    final lang = context.read<LanguageProvider>();
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: WebColors.bg,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(WebColors.radiusLg),
          side: const BorderSide(color: WebColors.border),
        ),
        title: Text(lang.translate('feed.confirmDelete'), style: const TextStyle(color: WebColors.text)),
        content: Text(lang.translate('feed.confirmDeleteBody'), style: const TextStyle(color: WebColors.textSecondary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text(lang.translate('perfil.cancel'), style: const TextStyle(color: WebColors.textMuted))),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: Text(lang.translate('common.delete'), style: const TextStyle(color: WebColors.danger))),
        ],
      ),
    );
    if (ok == true) {
      await PostService.deletar(widget.post.id);
      widget.onDeleted();
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return GlassContainer(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(lang),
          if (widget.post.conteudo.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              widget.post.conteudo,
              style: const TextStyle(fontSize: 14, color: WebColors.textSecondary, height: 1.5),
            ),
          ],
          if (widget.post.imagem != null) ...[
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(WebColors.radiusMd),
              child: GestureDetector(
                onDoubleTap: _curtir,
                child: CachedNetworkImage(
                  imageUrl: widget.post.imagem!,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  placeholder: (_, __) => const SizedBox(
                      height: 220,
                      child: Center(child: CircularProgressIndicator(color: WebColors.primary))),
                ),
              ),
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              _pillButton(
                icon: AnimatedScale(
                  scale: _heartBig ? 1.35 : 1.0,
                  duration: const Duration(milliseconds: 140),
                  curve: Curves.easeOut,
                  onEnd: () {
                    if (mounted && _heartBig) setState(() => _heartBig = false);
                  },
                  child: Icon(_jaCurtiu ? Icons.favorite : Icons.favorite_border,
                      size: 16, color: _jaCurtiu ? WebColors.danger : WebColors.textMuted),
                ),
                label: '$_curtidas',
                active: _jaCurtiu,
                onTap: _savingLike ? null : _curtir,
              ),
              const SizedBox(width: 8),
              _pillButton(
                icon: const Icon(Icons.chat_bubble_outline, size: 15, color: WebColors.textMuted),
                label: '${_comentarios.length}',
                onTap: () => setState(() => _showComments = !_showComments),
              ),
            ],
          ),
          if (_showComments) _buildComments(lang),
        ],
      ),
    );
  }

  Widget _buildHeader(LanguageProvider lang) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        GestureDetector(
          onTap: () => Navigator.pushNamed(context, '/perfil/${widget.post.idUsuario}'),
          child: AvatarWidget(
            fotoUrl: widget.post.fotoPerfil,
            iniciais: widget.post.nome.isNotEmpty ? widget.post.nome[0].toUpperCase() : '?',
            radius: 18,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: GestureDetector(
            onTap: () => Navigator.pushNamed(context, '/perfil/${widget.post.idUsuario}'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(widget.post.nome, style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 14)),
                Text(_formatarData(widget.post.dataCriacao, lang), style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
              ],
            ),
          ),
        ),
        if (widget.post.idUsuario == widget.meId)
          IconButton(
            visualDensity: VisualDensity.compact,
            icon: const Icon(Icons.close, color: WebColors.textMuted, size: 18),
            onPressed: _confirmDelete,
          ),
      ],
    );
  }

  Widget _pillButton({required Widget icon, required String label, VoidCallback? onTap, bool active = false}) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(WebColors.radiusPill),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            border: Border.all(color: active ? WebColors.danger.withValues(alpha: 0.35) : WebColors.border),
            borderRadius: BorderRadius.circular(WebColors.radiusPill),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              icon,
              const SizedBox(width: 5),
              Text(label, style: TextStyle(color: active ? WebColors.danger : WebColors.textMuted, fontSize: 13)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildComments(LanguageProvider lang) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 10),
        ..._comentarios.map((c) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  AvatarWidget(fotoUrl: c.fotoPerfil, iniciais: c.nome.isNotEmpty ? c.nome[0].toUpperCase() : '?', radius: 13),
                  const SizedBox(width: 8),
                  Expanded(
                    child: RichText(
                      text: TextSpan(
                        style: const TextStyle(fontSize: 13, color: WebColors.textSecondary, height: 1.5),
                        children: [
                          TextSpan(text: '${c.nome} ', style: const TextStyle(fontWeight: FontWeight.w700, color: WebColors.text)),
                          TextSpan(text: c.conteudo),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            )),
        Container(
          decoration: BoxDecoration(
            color: WebColors.surface2,
            borderRadius: BorderRadius.circular(WebColors.radiusPill),
            border: Border.all(color: WebColors.border),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _comentCtrl,
                  style: const TextStyle(color: WebColors.text, fontSize: 13),
                  decoration: InputDecoration(
                    filled: false,
                    hintText: lang.translate('feed.addComment'),
                    hintStyle: const TextStyle(color: WebColors.textMuted),
                    border: InputBorder.none,
                    enabledBorder: InputBorder.none,
                    focusedBorder: InputBorder.none,
                    contentPadding: EdgeInsets.zero,
                    isDense: true,
                  ),
                  onSubmitted: (_) => _enviarComentario(),
                  textInputAction: TextInputAction.send,
                ),
              ),
              const SizedBox(width: 8),
              _commenting
                  ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2, color: WebColors.accent))
                  : GestureDetector(
                      onTap: _enviarComentario,
                      child: Text(lang.translate('feed.publish'),
                          style: const TextStyle(color: WebColors.primary, fontWeight: FontWeight.w700, fontSize: 13)),
                    ),
            ],
          ),
        ),
      ],
    );
  }

  /// Mesma lógica de `formatarData()` em feed.html — exceto que aqui o
  /// sufixo já carrega o idioma inteiro ("min atrás"/"min ago"), então não
  /// precisa do prefixo "há" fixo em português que o site usa mesmo na
  /// versão em inglês (o que lá vira "5 min ago" com um "há" solto).
  String _formatarData(String iso, LanguageProvider lang) {
    try {
      final d = DateTime.parse(iso).toLocal();
      final diff = DateTime.now().difference(d).inSeconds;
      if (diff < 60) return lang.translate('feed.date.now');
      if (diff < 3600) return '${diff ~/ 60}${lang.translate('feed.date.min')}';
      if (diff < 86400) return '${diff ~/ 3600}${lang.translate('feed.date.hour')}';
      if (diff < 604800) return '${diff ~/ 86400}${lang.translate('feed.date.days')}';
      return DateFormat.yMd(lang.locale.toString()).format(d);
    } catch (_) {
      return iso;
    }
  }
}
