import 'package:dio/dio.dart';
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

  static Future<Post> criar({
    required String conteudo,
    String? imagemPath,
    String? imagemMime,
  }) async {
    final form = FormData.fromMap({
      'conteudo': conteudo,
      if (imagemPath != null)
        'imagem': await MultipartFile.fromFile(
          imagemPath,
          filename: imagemPath.split('/').last,
          contentType: DioMediaType.parse(imagemMime ?? 'image/jpeg'),
        ),
    });
    final r = await dio.post('/posts', data: form);
    _check(r);
    return Post.fromJson(r.data as Map<String, dynamic>);
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
