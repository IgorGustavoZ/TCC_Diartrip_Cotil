import 'dart:typed_data';

import 'package:crop_your_image/crop_your_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../providers/language_provider.dart';

/// Shows a full-screen-style crop dialog.
/// [aspectRatio] 1.0 = square (profile), null = free (group photos).
/// Returns the cropped [Uint8List] (PNG) or null if the user cancelled.
Future<Uint8List?> showImageCropperModal(
  BuildContext context,
  Uint8List imageBytes, {
  double? aspectRatio = 1.0,
}) {
  return showDialog<Uint8List>(
    context: context,
    barrierDismissible: false,
    barrierColor: Colors.black87,
    builder: (_) => _CropperDialog(
      imageBytes: imageBytes,
      aspectRatio: aspectRatio,
    ),
  );
}

class _CropperDialog extends StatefulWidget {
  final Uint8List imageBytes;
  final double? aspectRatio;

  const _CropperDialog({required this.imageBytes, this.aspectRatio});

  @override
  State<_CropperDialog> createState() => _CropperDialogState();
}

class _CropperDialogState extends State<_CropperDialog> {
  final _controller = CropController();
  bool _cropping = false;

  void _confirm() {
    if (_cropping) return;
    setState(() => _cropping = true);
    _controller.crop();
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.read<LanguageProvider>();
    final screen = MediaQuery.of(context).size;

    // Responsive crop area: fills mobile, capped on large screens
    final cropSize = (screen.shortestSide * 0.88).clamp(220.0, 520.0);

    return Dialog(
      backgroundColor: AppTheme.background,
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 32),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Title bar
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 14),
            child: Text(
              lang.translate('cropper.title'),
              style: const TextStyle(
                color: AppTheme.onSurface,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),

          // Crop canvas
          Container(
            width: cropSize,
            height: cropSize,
            clipBehavior: Clip.hardEdge,
            decoration: const BoxDecoration(color: Colors.black),
            child: Crop(
              controller: _controller,
              image: widget.imageBytes,
              aspectRatio: widget.aspectRatio,
              baseColor: Colors.black,
              maskColor: Colors.black54,
              onCropped: (croppedData) {
                if (!mounted) return;
                Navigator.of(context).pop(croppedData);
              },
            ),
          ),

          // Action buttons
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
            child: Row(
              children: [
                Expanded(
                  flex: 3,
                  child: ElevatedButton(
                    onPressed: _cropping ? null : _confirm,
                    child: _cropping
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : Text(lang.translate('cropper.usePhoto')),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 2,
                  child: OutlinedButton(
                    onPressed: _cropping
                        ? null
                        : () => Navigator.of(context).pop(null),
                    child: Text(lang.translate('cropper.cancel')),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
