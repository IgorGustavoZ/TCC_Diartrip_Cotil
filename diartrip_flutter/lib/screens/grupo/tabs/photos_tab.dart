import 'dart:typed_data';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../../../core/app_logger.dart';
import '../../../core/web_style.dart';
import '../../../models/foto.dart';
import '../../../providers/language_provider.dart';
import '../../../services/foto_service.dart';
import '../../../widgets/image_cropper_modal.dart';

class PhotosTab extends StatefulWidget {
  final int idGrupo;
  final int meId;
  /// Recarrega o dashboard compartilhado no [ViagemScreen] — o painel Admin
  /// mostra o total de fotos enviadas, que fica desatualizado sem isso.
  final Future<void> Function() onReload;
  const PhotosTab({super.key, required this.idGrupo, required this.meId, required this.onReload});
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
  /// Bytes da foto recém-recortada, mostrados na hora (antes mesmo do
  /// upload terminar) pra não parecer que "a foto não aparece imediatamente"
  /// — some assim que a lista recarregada do servidor já traz a foto real.
  Uint8List? _pendingPreview;

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
        .pickImage(source: ImageSource.gallery, imageQuality: 100);
    if (f == null || !mounted) return;

    final originalBytes = await f.readAsBytes();
    if (!mounted) return;

    // Free aspect ratio for group photos
    final croppedBytes = await showImageCropperModal(
      context,
      originalBytes,
      aspectRatio: null,
    );
    if (croppedBytes == null || !mounted) return;

    setState(() {
      _uploading = true;
      _pendingPreview = croppedBytes;
    });
    try {
      await FotoService.upload(
        idGrupo: widget.idGrupo,
        filePath: f.path,
        filename: 'group_photo.png',
        mimeType: 'image/png',
        bytes: croppedBytes,
      );
      await _load();
      if (mounted) setState(() => _pendingPreview = null);
      await widget.onReload();
    } catch (e) {
      if (mounted) {
        setState(() => _pendingPreview = null);
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  Future<void> _confirmarDelete(int idFoto) async {
    final lang = context.read<LanguageProvider>();
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: WebColors.bg2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(WebColors.radiusLg)),
        title: Text(lang.translate('photos.deleteTitle'), style: const TextStyle(color: WebColors.text)),
        content: Text(lang.translate('photos.deleteDesc'), style: const TextStyle(color: WebColors.textSecondary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              style: TextButton.styleFrom(foregroundColor: WebColors.textMuted),
              child: Text(lang.translate('photos.cancel'))),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: WebColors.danger),
            child: Text(lang.translate('photos.delete'), style: const TextStyle(fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await FotoService.deletar(idFoto);
      await _load();
      await widget.onReload();
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
    final lang = context.watch<LanguageProvider>();
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton(
        mini: true,
        backgroundColor: WebColors.primary,
        onPressed: _uploading ? null : _upload,
        tooltip: lang.translate('photos.addTooltip'),
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
          ? const Center(child: CircularProgressIndicator(color: WebColors.primary))
          : RefreshIndicator(
              onRefresh: _load,
              color: WebColors.primary,
              backgroundColor: WebColors.bg,
              child: _fotos.isEmpty && _pendingPreview == null
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.photo_library_outlined,
                              size: 48, color: WebColors.textMuted),
                          const SizedBox(height: 12),
                          Text(lang.translate('photos.empty'),
                              style: const TextStyle(color: WebColors.textMuted)),
                          const SizedBox(height: 4),
                          Text(lang.translate('photos.hint'),
                              style: const TextStyle(
                                  color: WebColors.textMuted,
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
                      itemCount: _fotos.length + (_pendingPreview != null ? 1 : 0),
                      itemBuilder: (_, i) {
                        if (_pendingPreview != null && i == 0) {
                          return ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Stack(
                              fit: StackFit.expand,
                              children: [
                                Image.memory(_pendingPreview!, fit: BoxFit.cover),
                                Container(
                                  color: Colors.black.withValues(alpha: 0.35),
                                  child: const Center(
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                  ),
                                ),
                              ],
                            ),
                          );
                        }
                        final foto = _fotos[i - (_pendingPreview != null ? 1 : 0)];
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
                                    color: WebColors.surface2,
                                    child: const Center(
                                      child: CircularProgressIndicator(
                                          strokeWidth: 2),
                                    ),
                                  ),
                                  errorWidget: (_, __, ___) => Container(
                                    color: WebColors.surface2,
                                    child: const Icon(
                                      Icons.broken_image_outlined,
                                      color: WebColors.textMuted,
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
                                    child: MouseRegion(
                                      cursor: SystemMouseCursors.click,
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
