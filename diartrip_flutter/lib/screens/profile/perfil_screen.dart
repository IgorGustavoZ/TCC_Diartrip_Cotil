import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:timeago/timeago.dart' as timeago;
import '../../core/theme.dart';
import '../../models/post.dart';
import '../../models/usuario.dart';
import '../../providers/auth_provider.dart';
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
        mimeType: 'image/jpeg',
        bytes: bytes,
      );
      setState(() => _usuario = Usuario(
            id: _usuario!.id,
            nome: _usuario!.nome,
            email: _usuario!.email,
            bio: _usuario!.bio,
            fotoPerfil: url,
            dataCriacao: _usuario!.dataCriacao,
            seguidores: _seguidores,
            seguindo: _seguindo,
          ));
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
    return Scaffold(
      appBar: AppBar(
        title: Text(_usuario?.nome ?? (_isMe ? 'My Profile' : 'Profile'),
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
                  SliverToBoxAdapter(child: _buildHeader()),
                  const SliverToBoxAdapter(
                    child: Divider(height: 1),
                  ),
                  _buildGrid(),
                ],
              ),
            ),
    );
  }

  // ── Header Instagram-like ─────────────────────────────────────────────────

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Avatar (left) + Stats (right)
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
                    _StatCol(label: 'Posts', value: _posts.length),
                    GestureDetector(
                      onTap: () => _showListaUsuarios(
                        'Followers',
                        () => SocialService.listarSeguidores(_targetId),
                      ),
                      child: _StatCol(
                          label: 'Followers', value: _seguidores),
                    ),
                    GestureDetector(
                      onTap: () => _showListaUsuarios(
                        'Following',
                        () => SocialService.listarSeguindo(_targetId),
                      ),
                      child: _StatCol(
                          label: 'Following', value: _seguindo),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Nome
          Text(_usuario?.nome ?? '',
              style: const TextStyle(
                  fontWeight: FontWeight.w700, fontSize: 15)),
          // Bio
          if (_usuario?.bio?.isNotEmpty == true) ...[
            const SizedBox(height: 4),
            Text(_usuario!.bio!,
                style: const TextStyle(
                    color: AppTheme.onSurface, fontSize: 13)),
          ],
          if (_usuario?.dataCriacao != null) ...[
            const SizedBox(height: 4),
            Text(
              'Member since ${_memberSince(_usuario!.dataCriacao!)}',
              style: const TextStyle(
                  color: AppTheme.onSurfaceMuted, fontSize: 12),
            ),
          ],
          const SizedBox(height: 14),
          // Botão de ação (Follow / Edit Profile)
          if (_isMe && !_editando)
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: () => setState(() => _editando = true),
                child: const Text('Edit Profile'),
              ),
            ),
          if (_isMe && _editando) ...[
            TextField(
              controller: _nomeCtrl,
              decoration: const InputDecoration(labelText: 'Name'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _bioCtrl,
              decoration: const InputDecoration(labelText: 'Bio'),
              maxLines: 3,
              maxLength: 200,
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () =>
                        setState(() => _editando = false),
                    child: const Text('Cancel'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _saving ? null : _salvar,
                    child: _saving
                        ? const SizedBox(
                            height: 14,
                            width: 14,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white))
                        : const Text('Save'),
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
                      onPressed:
                          _savingFollow ? null : _toggleSeguir,
                      child: _savingFollow
                          ? const SizedBox(
                              height: 14,
                              width: 14,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2))
                          : const Text('Following'),
                    )
                  : ElevatedButton(
                      onPressed:
                          _savingFollow ? null : _toggleSeguir,
                      child: _savingFollow
                          ? const SizedBox(
                              height: 14,
                              width: 14,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white))
                          : const Text('Follow'),
                    ),
            ),
        ],
      ),
    );
  }

  // ── Grade de posts ────────────────────────────────────────────────────────

  Widget _buildGrid() {
    if (_posts.isEmpty) {
      return const SliverFillRemaining(
        child: Center(
          child: Text('No posts yet.',
              style: TextStyle(color: AppTheme.onSurfaceMuted)),
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

class _PostDetailSheet extends StatelessWidget {
  final Post post;
  final bool isMe;
  final VoidCallback onDeleted;
  const _PostDetailSheet(
      {required this.post, required this.isMe, required this.onDeleted});

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.65,
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
          if (post.imagem != null)
            CachedNetworkImage(
                imageUrl: post.imagem!,
                width: double.infinity,
                fit: BoxFit.cover),
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                RichText(
                  text: TextSpan(
                    style: const TextStyle(
                        fontSize: 14, color: AppTheme.onSurface),
                    children: [
                      TextSpan(
                          text: '${post.nome} ',
                          style: const TextStyle(
                              fontWeight: FontWeight.w700)),
                      TextSpan(text: post.conteudo),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Icon(Icons.favorite,
                        size: 14,
                        color: post.jaCurtiu
                            ? AppTheme.error
                            : AppTheme.onSurfaceMuted),
                    const SizedBox(width: 4),
                    Text('${post.curtidas} likes',
                        style: const TextStyle(
                            color: AppTheme.onSurfaceMuted,
                            fontSize: 12)),
                    const SizedBox(width: 12),
                    const Icon(Icons.chat_bubble_outline,
                        size: 14, color: AppTheme.onSurfaceMuted),
                    const SizedBox(width: 4),
                    Text('${post.comentarios.length} comments',
                        style: const TextStyle(
                            color: AppTheme.onSurfaceMuted,
                            fontSize: 12)),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  _relativo(post.dataCriacao),
                  style: const TextStyle(
                      color: AppTheme.onSurfaceMuted, fontSize: 11),
                ),
                if (isMe) ...[
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.delete_outline,
                          size: 16, color: AppTheme.error),
                      label: const Text('Delete post',
                          style: TextStyle(color: AppTheme.error)),
                      style: OutlinedButton.styleFrom(
                          side: const BorderSide(
                              color: AppTheme.error)),
                      onPressed: () async {
                        Navigator.pop(context);
                        await PostService.deletar(post.id);
                        onDeleted();
                      },
                    ),
                  ),
                ],
                if (post.comentarios.isNotEmpty) ...[
                  const Divider(height: 24),
                  const Text('Comments',
                      style: TextStyle(
                          fontWeight: FontWeight.w700, fontSize: 14)),
                  const SizedBox(height: 8),
                  ...post.comentarios.map((c) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: RichText(
                          text: TextSpan(
                            style: const TextStyle(
                                fontSize: 13,
                                color: AppTheme.onSurface),
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
                ],
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
            const Expanded(
              child: Center(
                child: Text('No users yet.',
                    style:
                        TextStyle(color: AppTheme.onSurfaceMuted)),
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
