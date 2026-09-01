import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../core/api_client.dart';
import '../models/usuario.dart';
class UsuarioService {
  static Future<Usuario> getMe() async {
    final r = await dio.get('/usuarios/me');
    _check(r);
    return Usuario.fromJson(r.data as Map<String, dynamic>);
  }

  static Future<Usuario> get(int id) async {
    final r = await dio.get('/usuarios/$id');
    _check(r);
    return Usuario.fromJson(r.data as Map<String, dynamic>);
  }

  static Future<void> criar({
    required String nome,
    required String email,
    required String senha,
  }) async {
    final r = await dio.post('/usuarios', data: {
      'nome': nome,
      'email': email,
      'senha': senha,
    });
    if (r.statusCode != 200 && r.statusCode != 201) {
      throw ApiException(apiError(r.data, 'Erro ao criar conta'), r.statusCode);
    }
  }

  static Future<Usuario> atualizar({
    required int id,
    required String nome,
    required String email,
    String? bio,
  }) async {
    final r = await dio.put('/usuarios/$id', data: {
      'nome': nome,
      'email': email,
      if (bio != null) 'bio': bio,
    });
    _check(r);
    return getMe();
  }

  static Future<String> atualizarFoto({
    required int id,
    required String filePath,
    String? filename,
    required String mimeType,
    required Uint8List bytes,
  }) async {
    final fname = filename ?? filePath.split('/').last;
    debugPrint('[UsuarioService.atualizarFoto] filename=$fname mime=$mimeType bytes=${bytes.length} web=$kIsWeb');
    
    final multipart = MultipartFile.fromBytes(
      bytes,
      filename: fname,
      contentType: DioMediaType.parse(mimeType),
    );

    final form = FormData.fromMap({'foto': multipart});
    final r = await dio.patch('/usuarios/$id/foto', data: form);
    _check(r);
    return (r.data as Map<String, dynamic>)['foto_perfil'] as String;
  }

  static Future<void> deletar(int id) async {
    final r = await dio.delete('/usuarios/$id');
    _check(r);
  }

  /// Igual ao PUT /usuarios/{id}/senha do config.html. Backend responde 401
  /// especificamente quando `senhaAtual` está errada — o chamador pode
  /// checar `e.statusCode` (via [ApiException]) pra rotear o erro pro campo
  /// certo, como o site faz.
  static Future<void> trocarSenha({
    required int id,
    required String senhaAtual,
    required String novaSenha,
  }) async {
    final r = await dio.put('/usuarios/$id/senha', data: {
      'senha_atual': senhaAtual,
      'nova_senha': novaSenha,
    });
    if (r.statusCode != 200) {
      throw ApiException(apiError(r.data, 'Erro ao alterar senha'), r.statusCode);
    }
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw ApiException(apiError(r.data, 'Erro ${r.statusCode}'), r.statusCode);
    }
  }
}
