import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';

Future<MultipartFile> createMultipartFile({
  required String filePath,
  required String filename,
  required String mimeType,
  required Uint8List bytes,
}) async {
  return MultipartFile.fromFile(
    filePath,
    filename: filename,
    contentType: DioMediaType.parse(mimeType),
  );
}
