import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:timeago/timeago.dart' as timeago;
import '../../core/theme.dart';
import '../../models/comentario.dart';
import '../../models/post.dart';
import '../../providers/auth_provider.dart';
import '../../services/post_service.dart';
import '../../services/social_service.dart';
import '../../widgets/app_drawer.dart';
import '../../widgets/avatar_widget.dart';

class FeedScreen extends StatefulWidget {
  const FeedScreen({super.key});
  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  List<Post> _posts = [];
  bool _loading = true;
  bool _showCreate = false;
  final _conteudoCtrl = TextEditingController();
  XFile? _imagem;
  bool _publishing = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _conteudoCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final p = await PostService.listarTodos();
      if (mounted) setState(() { _posts = p; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _pickImage() async {
    final f = await ImagePicker()
        .pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (f != null) setState(() => _imagem = f);
  }

  Future<void> _publish() async {
    final texto = _conteudoCtrl.text.trim();
    if (texto.isEmpty) return;
    setState(() => _publishing = true);
    try {
      await PostService.criar(
        conteudo: texto,
        imagemPath: _imagem?.path,
        imagemMime: _imagem != null ? 'image/jpeg' : null,
      );
      _conteudoCtrl.clear();
      setState(() { _imagem = null; _showCreate = false; });
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Diartrip',
            style: TextStyle(
                fontWeight: FontWeight.w800,
                fontSize: 22,
                letterSpacing: -0.5)),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_box_outlined, size: 26),
            tooltip: 'New post',
            onPressed: () => setState(() => _showCreate = !_showCreate),
          ),
          const SizedBox(width: 4),
        ],
      ),
      drawer: const AppDrawer(activeRoute: '/feed'),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                children: [
                  if (_showCreate)
                    _CreateCard(
                      me: me,
                      ctrl: _conteudoCtrl,
                      imagem: _imagem,
                      publishing: _publishing,
                      onPickImage: _pickImage,
                      onPublish: _publish,
                    ),
                  if (_posts.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(48),
                      child: Center(
                        child: Text('No posts yet. Be the first!',
                            style: TextStyle(
                                color: AppTheme.onSurfaceMuted)),
                      ),
                    )
                  else
                    ..._posts.map((p) => _PostCard(
                          key: ValueKey(p.id),
                          post: p,
                          meId: me?.id ?? 0,
                          onDeleted: _load,
                        )),
                ],
              ),
      ),
    );
  }
}

// ─── Criar post ───────────────────────────────────────────────────────────────

class _CreateCard extends StatelessWidget {
  final dynamic me;
  final TextEditingController ctrl;
  final XFile? imagem;
  final bool publishing;
  final VoidCallback onPickImage;
  final VoidCallback onPublish;

  const _CreateCard({
    required this.me,
    required this.ctrl,
    required this.imagem,
    required this.publishing,
    required this.onPickImage,
    required this.onPublish,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppTheme.surface,
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AvatarWidget(
                  fotoUrl: me?.fotoPerfil,
                  iniciais: me?.iniciais ?? '?',
                  radius: 18),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: ctrl,
                  maxLines: 3,
                  decoration: const InputDecoration(
                      hintText: "What's on your travel mind?"),
                ),
              ),
            ],
          ),
          if (imagem != null) ...[
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.network(imagem!.path,
                  height: 160, fit: BoxFit.cover),
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              IconButton(
                onPressed: onPickImage,
                icon: const Icon(Icons.photo_outlined,
                    color: AppTheme.onSurfaceMuted),
              ),
              const Spacer(),
              ElevatedButton(
                onPressed: publishing ? null : onPublish,
                style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 24, vertical: 10)),
                child: publishing
                    ? const SizedBox(
                        height: 14,
                        width: 14,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white))
                    : const Text('Share'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─── Post Card (estilo Instagram) ─────────────────────────────────────────────

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

// SEM SingleTickerProviderStateMixin — usa AnimatedScale que não precisa de controller
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
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete post?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Delete',
                  style: TextStyle(color: AppTheme.error))),
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── Header ──
        _buildHeader(),
        // ── Imagem (full-bleed, duplo toque para curtir) ──
        if (widget.post.imagem != null)
          GestureDetector(
            onDoubleTap: _curtir,
            child: CachedNetworkImage(
              imageUrl: widget.post.imagem!,
              width: double.infinity,
              fit: BoxFit.cover,
              placeholder: (_, __) => const SizedBox(
                  height: 240,
                  child: Center(child: CircularProgressIndicator())),
            ),
          ),
        // ── Barra de ações ──
        _buildActionBar(),
        // ── Curtidas ──
        if (_curtidas > 0)
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 0, 14, 4),
            child: Text(
              '$_curtidas ${_curtidas == 1 ? "like" : "likes"}',
              style: const TextStyle(
                  fontWeight: FontWeight.w700, fontSize: 13),
            ),
          ),
        // ── Legenda ──
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 2, 14, 4),
          child: RichText(
            text: TextSpan(
              style: const TextStyle(
                  fontSize: 14, color: AppTheme.onSurface),
              children: [
                TextSpan(
                  text: '${widget.post.nome} ',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                TextSpan(text: widget.post.conteudo),
              ],
            ),
          ),
        ),
        // ── Comentários ──
        _buildComments(),
        // ── Timestamp ──
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
          child: Text(
            _relativo(widget.post.dataCriacao),
            style: const TextStyle(
                color: AppTheme.onSurfaceMuted, fontSize: 11),
          ),
        ),
        Divider(height: 1, color: Colors.white.withValues(alpha: 0.07)),
      ],
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.pushNamed(
                context, '/perfil/${widget.post.idUsuario}'),
            child: AvatarWidget(
              fotoUrl: widget.post.fotoPerfil,
              iniciais: widget.post.nome.isNotEmpty
                  ? widget.post.nome[0].toUpperCase()
                  : '?',
              radius: 18,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: GestureDetector(
              onTap: () => Navigator.pushNamed(
                  context, '/perfil/${widget.post.idUsuario}'),
              child: Text(widget.post.nome,
                  style: const TextStyle(
                      fontWeight: FontWeight.w600, fontSize: 14)),
            ),
          ),
          if (widget.post.idUsuario == widget.meId)
            IconButton(
              icon: const Icon(Icons.more_horiz,
                  color: AppTheme.onSurfaceMuted),
              onPressed: _confirmDelete,
            ),
        ],
      ),
    );
  }

  Widget _buildActionBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      child: Row(
        children: [
          // ── Curtir ──
          InkWell(
            onTap: _savingLike ? null : _curtir,
            borderRadius: BorderRadius.circular(20),
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: AnimatedScale(
                scale: _heartBig ? 1.35 : 1.0,
                duration: const Duration(milliseconds: 140),
                curve: Curves.easeOut,
                onEnd: () {
                  if (mounted && _heartBig) {
                    setState(() => _heartBig = false);
                  }
                },
                child: Icon(
                  _jaCurtiu ? Icons.favorite : Icons.favorite_border,
                  color: _jaCurtiu ? AppTheme.error : AppTheme.onSurface,
                  size: 27,
                ),
              ),
            ),
          ),
          // ── Comentar ──
          InkWell(
            onTap: () => setState(() => _showComments = !_showComments),
            borderRadius: BorderRadius.circular(20),
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Icon(
                _showComments
                    ? Icons.chat_bubble
                    : Icons.chat_bubble_outline,
                color: _showComments
                    ? AppTheme.primary
                    : AppTheme.onSurface,
                size: 25,
              ),
            ),
          ),
          const Spacer(),
        ],
      ),
    );
  }

  Widget _buildComments() {
    if (!_showComments && _comentarios.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!_showComments && _comentarios.isNotEmpty)
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 0, 14, 4),
            child: GestureDetector(
              onTap: () => setState(() => _showComments = true),
              child: Text(
                'View all ${_comentarios.length} comment${_comentarios.length > 1 ? "s" : ""}',
                style: const TextStyle(
                    color: AppTheme.onSurfaceMuted, fontSize: 13),
              ),
            ),
          ),
        if (_showComments) ...[
          ..._comentarios.map((c) => Padding(
                padding: const EdgeInsets.fromLTRB(14, 3, 14, 0),
                child: RichText(
                  text: TextSpan(
                    style: const TextStyle(
                        fontSize: 13, color: AppTheme.onSurface),
                    children: [
                      TextSpan(
                          text: '${c.nome} ',
                          style: const TextStyle(
                              fontWeight: FontWeight.w700)),
                      TextSpan(text: c.conteudo),
                    ],
                  ),
                ),
              )),
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 8, 14, 4),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _comentCtrl,
                    style: const TextStyle(fontSize: 13),
                    decoration: const InputDecoration(
                      hintText: 'Add a comment…',
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
                    ? const SizedBox(
                        height: 16,
                        width: 16,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : GestureDetector(
                        onTap: _enviarComentario,
                        child: const Text('Post',
                            style: TextStyle(
                                color: AppTheme.primary,
                                fontWeight: FontWeight.w700,
                                fontSize: 13)),
                      ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  String _relativo(String iso) {
    try {
      return timeago.format(DateTime.parse(iso).toLocal());
    } catch (_) {
      return iso;
    }
  }
}
