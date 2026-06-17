import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:timeago/timeago.dart' as timeago;
import '../../core/theme.dart';
import '../../models/post.dart';
import '../../models/usuario.dart';
import '../../models/comentario.dart';
import '../../providers/auth_provider.dart';
import '../../providers/language_provider.dart';
import '../../services/post_service.dart';
import '../../services/social_service.dart';
import '../../services/usuario_service.dart';
import '../../widgets/app_drawer.dart';
import '../../widgets/avatar_widget.dart';

class PerfilScreen extends StatefulWidget {
  final int? idUsuario;
  const PerfilScreen({super.key, this.idUsuario});
  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  Usuario? _usuario;
  List<Post> _posts = [];
  bool _loading = true;
  bool _editando = false;
  final _nomeCtrl = TextEditingController();
  final _bioCtrl = TextEditingController();
  bool _saving = false;

  late int _targetId;
  late bool _isMe;

  bool _jaSegue = false;
  int _seguidores = 0;
  int _seguindo = 0;
  bool _savingFollow = false;

  @override
  void initState() {
    super.initState();
    final meId = context.read<AuthProvider>().usuario?.id ?? 0;
    _targetId = widget.idUsuario ?? meId;
    _isMe = _targetId == meId;
    _load();
  }

  @override
  void dispose() {
    _nomeCtrl.dispose();
    _bioCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final results = await Future.wait([
        _isMe ? UsuarioService.getMe() : UsuarioService.get(_targetId),
        PostService.listarPorUsuario(_targetId),
      ]);
      _usuario = results[0] as Usuario;
      _posts = results[1] as List<Post>;
      _nomeCtrl.text = _usuario!.nome;
      _bioCtrl.text = _usuario!.bio ?? '';
      _seguidores = _usuario!.seguidores;
      _seguindo = _usuario!.seguindo;
      _jaSegue = _usuario!.jaSegue ?? false;
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _salvar() async {
    setState(() => _saving = true);
    try {
      final atualizado = await UsuarioService.atualizar(
        id: _targetId,
        nome: _nomeCtrl.text.trim(),
        email: _usuario!.email ?? '',
        bio: _bioCtrl.text.trim(),
      );
      if (!mounted) return;
      context.read<AuthProvider>().updateUsuario(atualizado);
      setState(() { _usuario = atualizado; _editando = false; });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _trocarFoto() async {
    final f = await ImagePicker()
        .pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (f == null || !mounted) return;
    try {
      final bytes = await f.readAsBytes();
      final url = await UsuarioService.atualizarFoto(
        id: _targetId,
        filePath: f.path,
        filename: f.name,
        mimeType: f.mimeType ?? 'image/jpeg',
        bytes: bytes,
      );
      if (!mounted) return;
      final atualizado = Usuario(
        id: _usuario!.id,
        nome: _usuario!.nome,
        email: _usuario!.email,
        bio: _usuario!.bio,
        fotoPerfil: url,
        dataCriacao: _usuario!.dataCriacao,
        seguidores: _seguidores,
        seguindo: _seguindo,
      );
      context.read<AuthProvider>().updateUsuario(atualizado);
      setState(() => _usuario = atualizado);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  Future<void> _toggleSeguir() async {
    if (_savingFollow) return;
    setState(() => _savingFollow = true);
    try {
      final res = await SocialService.seguirUsuario(_targetId);
      if (!mounted) return;
      setState(() {
        _jaSegue = res['seguindo'] as bool;
        _seguidores = res['total_seguidores'] as int;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _savingFollow = false);
    }
  }

  void _showListaUsuarios(
    String titulo,
    Future<List<Map<String, dynamic>>> Function() carregarFn,
  ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) =>
          _ListaUsuariosSheet(titulo: titulo, carregarFn: carregarFn),
    );
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return Scaffold(
      appBar: AppBar(
        title: Text(_usuario?.nome ?? (_isMe ? lang.translate('perfil.myProfile') : lang.translate('perfil.profile')),
            style: const TextStyle(fontWeight: FontWeight.w700)),
        actions: _isMe
            ? [
                IconButton(
                  icon: const Icon(Icons.settings_outlined),
                  onPressed: () =>
                      Navigator.pushNamed(context, '/config'),
                ),
              ]
            : null,
      ),
      drawer: _isMe ? AppDrawer(activeRoute: '/perfil/$_targetId') : null,
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: CustomScrollView(
                slivers: [
                  SliverToBoxAdapter(child: _buildHeader(lang)),
                  const SliverToBoxAdapter(
                    child: Divider(height: 1),
                  ),
                  _buildGrid(lang),
                ],
              ),
            ),
    );
  }

  // ── Header Instagram-like ─────────────────────────────────────────────────

  Widget _buildHeader(LanguageProvider lang) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Stack(
                children: [
                  AvatarWidget(
                    fotoUrl: _usuario?.fotoPerfil,
                    iniciais: _usuario?.iniciais ?? '?',
                    radius: 42,
                    onTap: _isMe ? _trocarFoto : null,
                  ),
                  if (_isMe)
                    Positioned(
                      right: 0,
                      bottom: 0,
                      child: Container(
                        padding: const EdgeInsets.all(4),
                        decoration: const BoxDecoration(
                            color: AppTheme.primary,
                            shape: BoxShape.circle),
                        child: const Icon(Icons.camera_alt,
                            size: 13, color: Colors.white),
                      ),
                    ),
                ],
              ),
              const SizedBox(width: 24),
              Expanded(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _StatCol(label: lang.translate('perfil.posts'), value: _posts.length),
                    GestureDetector(
                      onTap: () => _showListaUsuarios(
                        lang.translate('perfil.followers'),
                        () => SocialService.listarSeguidores(_targetId),
                      ),
                      child: _StatCol(label: lang.translate('perfil.followers'), value: _seguidores),
                    ),
                    GestureDetector(
                      onTap: () => _showListaUsuarios(
                        lang.translate('perfil.following'),
                        () => SocialService.listarSeguindo(_targetId),
                      ),
                      child: _StatCol(label: lang.translate('perfil.following'), value: _seguindo),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(_usuario?.nome ?? '',
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
          if (_usuario?.bio?.isNotEmpty == true) ...[
            const SizedBox(height: 4),
            Text(_usuario!.bio!,
                style: const TextStyle(color: AppTheme.onSurface, fontSize: 13)),
          ],
          if (_usuario?.dataCriacao != null) ...[
            const SizedBox(height: 4),
            Text(
              '${lang.translate('perfil.memberSince')} ${_memberSince(_usuario!.dataCriacao!)}',
              style: const TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 12),
            ),
          ],
          const SizedBox(height: 14),
          if (_isMe && !_editando)
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: () => setState(() => _editando = true),
                child: Text(lang.translate('perfil.editProfile')),
              ),
            ),
          if (_isMe && _editando) ...[
            TextField(
              controller: _nomeCtrl,
              decoration: InputDecoration(labelText: lang.translate('perfil.name')),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _bioCtrl,
              decoration: InputDecoration(labelText: lang.translate('perfil.bio')),
              maxLines: 3,
              maxLength: 200,
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => setState(() => _editando = false),
                    child: Text(lang.translate('perfil.cancel')),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _saving ? null : _salvar,
                    child: _saving
                        ? const SizedBox(
                            height: 14, width: 14,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text(lang.translate('perfil.save')),
                  ),
                ),
              ],
            ),
          ],
          if (!_isMe)
            SizedBox(
              width: double.infinity,
              child: _jaSegue
                  ? OutlinedButton(
                      onPressed: _savingFollow ? null : _toggleSeguir,
                      child: _savingFollow
                          ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2))
                          : Text(lang.translate('perfil.followingBtn')),
                    )
                  : ElevatedButton(
                      onPressed: _savingFollow ? null : _toggleSeguir,
                      child: _savingFollow
                          ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : Text(lang.translate('perfil.follow')),
                    ),
            ),
        ],
      ),
    );
  }

  // ── Grade de posts ────────────────────────────────────────────────────────

  Widget _buildGrid(LanguageProvider lang) {
    if (_posts.isEmpty) {
      return SliverFillRemaining(
        child: Center(
          child: Text(lang.translate('perfil.noPosts'),
              style: const TextStyle(color: AppTheme.onSurfaceMuted)),
        ),
      );
    }
    return SliverGrid(
      delegate: SliverChildBuilderDelegate(
        (ctx, i) => _PostThumb(post: _posts[i], isMe: _isMe,
            onDeleted: _load),
        childCount: _posts.length,
      ),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        crossAxisSpacing: 2,
        mainAxisSpacing: 2,
      ),
    );
  }

  String _memberSince(String iso) {
    try {
      return DateFormat('MMMM yyyy').format(DateTime.parse(iso));
    } catch (_) {
      return iso;
    }
  }
}

// ─── Thumb da grade ───────────────────────────────────────────────────────────

class _PostThumb extends StatelessWidget {
  final Post post;
  final bool isMe;
  final VoidCallback onDeleted;
  const _PostThumb(
      {required this.post, required this.isMe, required this.onDeleted});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => _showDetail(context),
      child: Stack(
        fit: StackFit.expand,
        children: [
          if (post.imagem != null)
            CachedNetworkImage(
                imageUrl: post.imagem!, fit: BoxFit.cover)
          else
            Container(
              color: AppTheme.surfaceVariant,
              child: const Center(
                child: Icon(Icons.article_outlined,
                    color: AppTheme.onSurfaceMuted, size: 28),
              ),
            ),
          // Badge de curtidas
          Positioned(
            left: 6,
            bottom: 6,
            child: Row(
              children: [
                const Icon(Icons.favorite, size: 12, color: Colors.white),
                const SizedBox(width: 3),
                Text('${post.curtidas}',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        shadows: [Shadow(blurRadius: 4)])),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showDetail(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) => _PostDetailSheet(
          post: post, isMe: isMe, onDeleted: onDeleted),
    );
  }
}

// ─── Detalhe do post (bottom sheet) ──────────────────────────────────────────

class _PostDetailSheet extends StatefulWidget {
  final Post post;
  final bool isMe;
  final VoidCallback onDeleted;
  const _PostDetailSheet(
      {required this.post, required this.isMe, required this.onDeleted});

  @override
  State<_PostDetailSheet> createState() => _PostDetailSheetState();
}

class _PostDetailSheetState extends State<_PostDetailSheet> {
  late bool _jaCurtiu;
  late int _curtidas;
  late List<Comentario> _comentarios;
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

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      expand: false,
      builder: (_, ctrl) => ListView(
        controller: ctrl,
        children: [
          const SizedBox(height: 8),
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                  color: AppTheme.onSurfaceMuted.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(2)),
            ),
          ),
          if (widget.post.imagem != null)
            CachedNetworkImage(
                imageUrl: widget.post.imagem!,
                width: double.infinity,
                fit: BoxFit.cover),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Legenda
                RichText(
                  text: TextSpan(
                    style: const TextStyle(fontSize: 14, color: AppTheme.onSurface),
                    children: [
                      TextSpan(
                          text: '${widget.post.nome} ',
                          style: const TextStyle(fontWeight: FontWeight.w700)),
                      TextSpan(text: widget.post.conteudo),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                // Barra de ações: curtir
                Row(
                  children: [
                    InkWell(
                      onTap: _savingLike ? null : _curtir,
                      borderRadius: BorderRadius.circular(20),
                      child: Padding(
                        padding: const EdgeInsets.all(6),
                        child: AnimatedScale(
                          scale: _heartBig ? 1.35 : 1.0,
                          duration: const Duration(milliseconds: 140),
                          curve: Curves.easeOut,
                          onEnd: () {
                            if (mounted && _heartBig) setState(() => _heartBig = false);
                          },
                          child: Icon(
                            _jaCurtiu ? Icons.favorite : Icons.favorite_border,
                            color: _jaCurtiu ? AppTheme.error : AppTheme.onSurface,
                            size: 26,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    if (_curtidas > 0)
                      Text(
                        '$_curtidas ${_curtidas == 1 ? lang.translate('perfil.like') : lang.translate('perfil.likes')}',
                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                      ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  _relativo(widget.post.dataCriacao),
                  style: const TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 11),
                ),
                if (widget.isMe) ...[
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.delete_outline, size: 16, color: AppTheme.error),
                      label: Text(lang.translate('perfil.deletePost'),
                          style: const TextStyle(color: AppTheme.error)),
                      style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: AppTheme.error)),
                      onPressed: () async {
                        Navigator.pop(context);
                        await PostService.deletar(widget.post.id);
                        widget.onDeleted();
                      },
                    ),
                  ),
                ],
                // Seção de comentários — sempre visível
                const Divider(height: 24),
                Text(lang.translate('perfil.comments'),
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                const SizedBox(height: 8),
                ..._comentarios.map((c) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: RichText(
                        text: TextSpan(
                          style: const TextStyle(fontSize: 13, color: AppTheme.onSurface),
                          children: [
                            TextSpan(
                                text: '${c.nome} ',
                                style: const TextStyle(fontWeight: FontWeight.w700)),
                            TextSpan(text: c.conteudo),
                          ],
                        ),
                      ),
                    )),
                // Input de comentário
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _comentCtrl,
                          style: const TextStyle(fontSize: 13),
                          decoration: InputDecoration(
                            hintText: lang.translate('perfil.addComment'),
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
                              height: 16, width: 16,
                              child: CircularProgressIndicator(strokeWidth: 2))
                          : GestureDetector(
                              onTap: _enviarComentario,
                              child: Text(lang.translate('perfil.post'),
                                  style: const TextStyle(
                                      color: AppTheme.primary,
                                      fontWeight: FontWeight.w700,
                                      fontSize: 13)),
                            ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
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

// ─── Coluna de estatística ────────────────────────────────────────────────────

class _StatCol extends StatelessWidget {
  final String label;
  final int value;
  const _StatCol({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('$value',
            style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: AppTheme.onSurface)),
        const SizedBox(height: 2),
        Text(label,
            style: const TextStyle(
                color: AppTheme.onSurfaceMuted, fontSize: 12)),
      ],
    );
  }
}

// ─── Lista de seguidores / seguindo (bottom sheet) ────────────────────────────

class _ListaUsuariosSheet extends StatefulWidget {
  final String titulo;
  final Future<List<Map<String, dynamic>>> Function() carregarFn;
  const _ListaUsuariosSheet(
      {required this.titulo, required this.carregarFn});

  @override
  State<_ListaUsuariosSheet> createState() => _ListaUsuariosSheetState();
}

class _ListaUsuariosSheetState extends State<_ListaUsuariosSheet> {
  List<Map<String, dynamic>> _lista = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final result = await widget.carregarFn();
      if (mounted) setState(() { _lista = result; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.5,
      minChildSize: 0.3,
      maxChildSize: 0.9,
      expand: false,
      builder: (_, scrollCtrl) => Column(
        children: [
          const SizedBox(height: 10),
          Container(
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: AppTheme.onSurfaceMuted.withValues(alpha: 0.4),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 14),
          Text(widget.titulo,
              style: const TextStyle(
                  fontWeight: FontWeight.w700, fontSize: 16)),
          const Divider(height: 20),
          if (_loading)
            const Expanded(
                child: Center(child: CircularProgressIndicator()))
          else if (_lista.isEmpty)
            Expanded(
              child: Center(
                child: Text(
                    context.watch<LanguageProvider>().translate('perfil.noUsers'),
                    style: const TextStyle(color: AppTheme.onSurfaceMuted)),
              ),
            )
          else
            Expanded(
              child: ListView.builder(
                controller: scrollCtrl,
                itemCount: _lista.length,
                itemBuilder: (ctx, i) {
                  final u = _lista[i];
                  final nome = u['nome'] as String? ?? '';
                  final foto = u['foto_perfil'] as String?;
                  final id = u['id_usuario'] as int?;
                  return ListTile(
                    leading: AvatarWidget(
                      fotoUrl: foto,
                      iniciais: nome.isNotEmpty
                          ? nome[0].toUpperCase()
                          : '?',
                      radius: 20,
                    ),
                    title: Text(nome,
                        style: const TextStyle(
                            fontWeight: FontWeight.w600)),
                    onTap: id != null
                        ? () {
                            Navigator.pop(ctx);
                            Navigator.pushNamed(ctx, '/perfil/$id');
                          }
                        : null,
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}
