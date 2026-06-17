import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';

/// Stub para criação de MultipartFile.
Future<MultipartFile> createMultipartFile({
  required String filePath,
  required String filename,
  required String mimeType,
  required Uint8List bytes,
}) => throw UnsupportedError('Cannot create multipart file');
