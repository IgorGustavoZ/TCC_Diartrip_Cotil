import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../core/api_client.dart';
import '../models/post.dart';
class PostService {
  static Future<List<Post>> listarTodos() async {
    final r = await dio.get('/posts');
    _check(r);
    return (r.data as List).map((e) => Post.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<List<Post>> listarPorUsuario(int idUsuario) async {
    final r = await dio.get('/posts/usuario/$idUsuario');
    _check(r);
    return (r.data as List).map((e) => Post.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<void> criar({
    required String conteudo,
    Uint8List? imagemBytes,
    String? imagemFilename,
    String? imagemMime,
  }) async {
    debugPrint('[PostService.criar] filename=$imagemFilename mime=$imagemMime bytes=${imagemBytes?.length}');
    
    MultipartFile? multipart;
    if (imagemBytes != null && imagemFilename != null) {
      multipart = MultipartFile.fromBytes(
        imagemBytes,
        filename: imagemFilename,
        contentType: DioMediaType.parse(imagemMime ?? 'image/jpeg'),
      );
    }

    final form = FormData.fromMap({
      'conteudo': conteudo,
      if (multipart != null) 'imagem': multipart,
    });
    final r = await dio.post('/posts', data: form);
    _check(r);
  }

  static Future<void> deletar(int id) async {
    final r = await dio.delete('/posts/$id');
    _check(r);
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro ${r.statusCode}');
    }
  }
}
