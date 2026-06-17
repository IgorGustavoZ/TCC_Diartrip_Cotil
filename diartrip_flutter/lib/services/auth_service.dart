import '../core/api_client.dart';
import '../models/usuario.dart';
import 'usuario_service.dart';

class AuthService {
  static Future<Usuario> login(String email, String senha) async {
    final r = await dio.post('/login', data: {'email': email, 'senha': senha});
    if (r.statusCode != 200) {
      // apiError() é seguro mesmo se r.data não for um Map.
      throw apiError(r.data, 'Credenciais inválidas');
    }
    return UsuarioService.getMe();
  }

  static Future<void> logout() async {
    try {
      await dio.post('/logout');
    } finally {
      await cookieJar.deleteAll();
    }
  }
}
