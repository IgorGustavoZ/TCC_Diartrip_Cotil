import 'package:flutter/material.dart';
import '../core/app_logger.dart';
import '../models/usuario.dart';
import '../services/auth_service.dart';
import '../services/usuario_service.dart';

class AuthProvider extends ChangeNotifier {
  Usuario? _usuario;
  bool _loading = false;

  Usuario? get usuario => _usuario;
  bool get isLoggedIn => _usuario != null;
  bool get loading => _loading;

  Future<void> tryAutoLogin() async {
    try {
      _usuario = await UsuarioService.getMe();
      notifyListeners();
    } catch (e, s) {
      // Sessão inativa ou rede indisponível — não é um erro fatal
      AppLogger.info('AuthProvider.tryAutoLogin', 'sessão inativa ou rede indisponível: $e');
      if (s != StackTrace.empty) {
        AppLogger.captureError('AuthProvider.tryAutoLogin', e, s, fatal: false);
      }
      _usuario = null;
    }
  }

  Future<void> login(String email, String senha) async {
    _loading = true;
    notifyListeners();
    try {
      _usuario = await AuthService.login(email, senha);
      notifyListeners();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await AuthService.logout();
    _usuario = null;
    notifyListeners();
  }

  void updateUsuario(Usuario u) {
    _usuario = u;
    notifyListeners();
  }
}
