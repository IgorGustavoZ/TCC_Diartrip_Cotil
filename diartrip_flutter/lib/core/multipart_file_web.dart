import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';

/// Implementação Web: usa estritamente fromBytes.
Future<MultipartFile> createMultipartFile({
  required String filePath,
  required String filename,
  required String mimeType,
  required Uint8List bytes,
}) async {
  return MultipartFile.fromBytes(
    bytes,
    filename: filename,
    contentType: DioMediaType.parse(mimeType),
  );
}
