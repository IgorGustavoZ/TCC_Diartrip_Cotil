import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/comentario.dart';

class SocialService {
  static Future<Map<String, dynamic>> curtirPost(int idPost) async {
    final r = await dio.post('/posts/$idPost/curtir');
    _check(r);
    return r.data as Map<String, dynamic>;
  }

  static Future<Comentario> comentarPost(int idPost, String conteudo) async {
    final r = await dio.post(
      '/posts/$idPost/comentar',
      data: {'conteudo': conteudo},
    );
    _check(r);
    return Comentario.fromJson(r.data as Map<String, dynamic>);
  }

  static Future<Map<String, dynamic>> seguirUsuario(int idUsuario) async {
    final r = await dio.post('/usuarios/$idUsuario/seguir');
    _check(r);
    return r.data as Map<String, dynamic>;
  }

  static Future<List<Map<String, dynamic>>> listarSeguidores(int idUsuario) async {
    final r = await dio.get('/usuarios/$idUsuario/seguidores');
    _check(r);
    return (r.data as List).cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> listarSeguindo(int idUsuario) async {
    final r = await dio.get('/usuarios/$idUsuario/seguindo');
    _check(r);
    return (r.data as List).cast<Map<String, dynamic>>();
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro ${r.statusCode}');
    }
  }
}
