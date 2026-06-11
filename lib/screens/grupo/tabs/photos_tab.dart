import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../../../core/app_logger.dart';
import 'package:image_picker/image_picker.dart';
import '../../../core/theme.dart';
import '../../../models/foto.dart';
import '../../../services/foto_service.dart';

class PhotosTab extends StatefulWidget {
  final int idGrupo;
  final int meId;
  const PhotosTab({super.key, required this.idGrupo, required this.meId});
  @override
  State<PhotosTab> createState() => _PhotosTabState();
}

class _PhotosTabState extends State<PhotosTab>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  List<Foto> _fotos = [];
  bool _loading = true;
  bool _uploading = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final f = await FotoService.listar(widget.idGrupo);
      if (mounted) setState(() { _fotos = f; _loading = false; });
    } catch (e, s) {
      AppLogger.captureError('PhotosTab._load', e, s);
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _upload() async {
    final f = await ImagePicker()
        .pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (f == null || !mounted) return;
    setState(() => _uploading = true);
    try {
      final bytes = await f.readAsBytes();
      await FotoService.upload(
        idGrupo: widget.idGrupo,
        filePath: f.path,
        mimeType: 'image/jpeg',
        bytes: bytes,
      );
      await _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  Future<void> _confirmarDelete(int idFoto) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete photo?'),
        content: const Text('This action cannot be undone.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppTheme.error),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await FotoService.deletar(idFoto);
      _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton(
        mini: true,
        onPressed: _uploading ? null : _upload,
        tooltip: 'Add photo',
        child: _uploading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                    color: Colors.white, strokeWidth: 2),
              )
            : const Icon(Icons.add_photo_alternate_outlined),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: _fotos.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.photo_library_outlined,
                              size: 48, color: AppTheme.onSurfaceMuted),
                          SizedBox(height: 12),
                          Text('No photos yet.',
                              style:
                                  TextStyle(color: AppTheme.onSurfaceMuted)),
                          SizedBox(height: 4),
                          Text('Tap + to add the first one.',
                              style: TextStyle(
                                  color: AppTheme.onSurfaceMuted,
                                  fontSize: 12)),
                        ],
                      ),
                    )
                  : GridView.builder(
                      padding: const EdgeInsets.fromLTRB(10, 10, 10, 80),
                      gridDelegate:
                          const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        crossAxisSpacing: 8,
                        mainAxisSpacing: 8,
                      ),
                      itemCount: _fotos.length,
                      itemBuilder: (_, i) {
                        final foto = _fotos[i];
                        final isMe = foto.idUsuario == widget.meId;
                        return GestureDetector(
                          onLongPress: isMe
                              ? () => _confirmarDelete(foto.id)
                              : null,
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Stack(
                              fit: StackFit.expand,
                              children: [
                                CachedNetworkImage(
                                  imageUrl: foto.caminhoArquivo,
                                  fit: BoxFit.cover,
                                  placeholder: (_, __) => Container(
                                    color: AppTheme.surfaceVariant,
                                    child: const Center(
                                      child: CircularProgressIndicator(
                                          strokeWidth: 2),
                                    ),
                                  ),
                                  errorWidget: (_, __, ___) => Container(
                                    color: AppTheme.surfaceVariant,
                                    child: const Icon(
                                      Icons.broken_image_outlined,
                                      color: AppTheme.onSurfaceMuted,
                                    ),
                                  ),
                                ),
                                Positioned(
                                  bottom: 0,
                                  left: 0,
                                  right: 0,
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 8, vertical: 5),
                                    decoration: BoxDecoration(
                                      gradient: LinearGradient(
                                        begin: Alignment.bottomCenter,
                                        end: Alignment.topCenter,
                                        colors: [
                                          Colors.black
                                              .withValues(alpha: 0.65),
                                          Colors.transparent,
                                        ],
                                      ),
                                    ),
                                    child: Text(
                                      foto.nomeUsuario ?? '',
                                      style: const TextStyle(
                                          color: Colors.white, fontSize: 11),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ),
                                if (isMe)
                                  Positioned(
                                    top: 4,
                                    right: 4,
                                    child: GestureDetector(
                                      onTap: () =>
                                          _confirmarDelete(foto.id),
                                      child: Container(
                                        padding: const EdgeInsets.all(4),
                                        decoration: BoxDecoration(
                                          color: Colors.black
                                              .withValues(alpha: 0.5),
                                          shape: BoxShape.circle,
                                        ),
                                        child: const Icon(
                                          Icons.delete_outline,
                                          color: Colors.white,
                                          size: 14,
                                        ),
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
    );
  }
}
