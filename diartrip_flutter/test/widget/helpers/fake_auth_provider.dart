import 'package:flutter/material.dart';
import 'package:diartrip_flutter/models/usuario.dart';
import 'package:diartrip_flutter/providers/auth_provider.dart';

/// AuthProvider falso para widget tests — sem dependência de rede.
class FakeAuthProvider extends ChangeNotifier implements AuthProvider {
  Usuario? _usuario;
  bool _loading = false;
  Exception? loginError;
  bool logoutCalled = false;

  void setUsuario(Usuario? u) {
    _usuario = u;
    notifyListeners();
  }

  void setLoading(bool v) {
    _loading = v;
    notifyListeners();
  }

  @override
  Usuario? get usuario => _usuario;

  @override
  bool get isLoggedIn => _usuario != null;

  @override
  bool get loading => _loading;

  @override
  Future<void> tryAutoLogin() async {
    // No-op em widget tests
  }

  @override
  Future<void> login(String email, String senha) async {
    _loading = true;
    notifyListeners();
    if (loginError != null) {
      _loading = false;
      notifyListeners();
      throw loginError!;
    }
    _loading = false;
    notifyListeners();
  }

  @override
  Future<void> logout() async {
    logoutCalled = true;
    _usuario = null;
    notifyListeners();
  }

  @override
  void updateUsuario(Usuario u) {
    _usuario = u;
    notifyListeners();
  }
}
