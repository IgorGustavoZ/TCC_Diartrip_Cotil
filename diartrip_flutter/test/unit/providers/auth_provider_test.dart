import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http_mock_adapter/http_mock_adapter.dart';

import 'package:diartrip_flutter/core/api_client.dart' as api;
import 'package:diartrip_flutter/models/usuario.dart';
import 'package:diartrip_flutter/providers/auth_provider.dart';

Map<String, dynamic> _usuarioJson({int id = 1, String nome = 'Teste User'}) => {
      'id_usuario': id,
      'nome': nome,
      'email': 'teste@example.com',
      'bio': null,
      'foto_perfil': null,
      'data_criacao': '2026-01-01T00:00:00',
    };

void main() {
  late DioAdapter dioAdapter;

  setUpAll(() {
    api.cookieJar = DefaultCookieJar();
    api.dio = Dio(BaseOptions(
      baseUrl: 'http://test.local',
      validateStatus: (status) => status != null && status < 500,
    ));
    dioAdapter = DioAdapter(dio: api.dio, matcher: const FullHttpRequestMatcher());
  });

  group('Estado inicial', () {
    test('começa não autenticado e sem loading', () {
      final p = AuthProvider();
      expect(p.isLoggedIn, isFalse);
      expect(p.loading, isFalse);
      expect(p.usuario, isNull);
    });
  });

  group('tryAutoLogin', () {
    test('seta usuario quando GET /usuarios/me retorna 200', () async {
      dioAdapter.onGet(
        '/usuarios/me',
        (server) => server.reply(200, _usuarioJson()),
      );
      final p = AuthProvider();
      await p.tryAutoLogin();
      expect(p.isLoggedIn, isTrue);
      expect(p.usuario?.nome, 'Teste User');
    });

    test('permanece não logado quando GET /usuarios/me retorna 401', () async {
      dioAdapter.onGet(
        '/usuarios/me',
        (server) => server.reply(401, {'detail': 'Não autenticado'}),
      );
      final p = AuthProvider();
      await p.tryAutoLogin();
      expect(p.isLoggedIn, isFalse);
      expect(p.usuario, isNull);
    });

    test('não lança exceção em erros de rede', () async {
      dioAdapter.onGet(
        '/usuarios/me',
        (server) => server.reply(500, {}),
      );
      final p = AuthProvider();
      // tryAutoLogin captura erros internamente
      await expectLater(p.tryAutoLogin(), completes);
      expect(p.isLoggedIn, isFalse);
    });
  });

  group('login', () {
    test('seta usuario após credenciais válidas', () async {
      dioAdapter
        ..onPost(
          '/login',
          (server) => server.reply(200, {'mensagem': 'OK', 'usuario_id': 1}),
          data: {'email': 'a@a.com', 'senha': 'Pass1234'},
        )
        ..onGet(
          '/usuarios/me',
          (server) => server.reply(200, _usuarioJson(nome: 'Login User')),
        );

      final p = AuthProvider();
      await p.login('a@a.com', 'Pass1234');

      expect(p.isLoggedIn, isTrue);
      expect(p.usuario?.nome, 'Login User');
      expect(p.loading, isFalse);
    });

    test('loading fica false mesmo após falha', () async {
      dioAdapter.onPost(
        '/login',
        (server) => server.reply(401, {'detail': 'Credenciais inválidas'}),
        data: {'email': 'x@x.com', 'senha': 'errado'},
      );
      final p = AuthProvider();
      try {
        await p.login('x@x.com', 'errado');
      } catch (_) {}
      expect(p.loading, isFalse);
    });

    test('notifica listeners ao fazer login', () async {
      dioAdapter
        ..onPost('/login', (server) => server.reply(200, {'usuario_id': 1}),
            data: {'email': 'b@b.com', 'senha': 'Pass1234'})
        ..onGet('/usuarios/me', (server) => server.reply(200, _usuarioJson()));

      final p = AuthProvider();
      int count = 0;
      p.addListener(() => count++);
      await p.login('b@b.com', 'Pass1234');
      expect(count, greaterThan(0));
    });
  });

  group('logout', () {
    test('limpa usuario após logout', () async {
      dioAdapter
        ..onPost('/login', (server) => server.reply(200, {'usuario_id': 1}),
            data: {'email': 'a@a.com', 'senha': 'Pass1234'})
        ..onGet('/usuarios/me', (server) => server.reply(200, _usuarioJson()))
        ..onPost('/logout', (server) => server.reply(200, {}));

      final p = AuthProvider();
      await p.login('a@a.com', 'Pass1234');
      expect(p.isLoggedIn, isTrue);

      await p.logout();
      expect(p.isLoggedIn, isFalse);
      expect(p.usuario, isNull);
    });

    test('notifica listeners ao deslogar', () async {
      dioAdapter
        ..onPost('/login', (server) => server.reply(200, {'usuario_id': 1}),
            data: {'email': 'c@c.com', 'senha': 'Pass1234'})
        ..onGet('/usuarios/me', (server) => server.reply(200, _usuarioJson()))
        ..onPost('/logout', (server) => server.reply(200, {}));

      final p = AuthProvider();
      await p.login('c@c.com', 'Pass1234');

      int count = 0;
      p.addListener(() => count++);
      await p.logout();
      expect(count, greaterThan(0));
    });
  });

  group('updateUsuario', () {
    test('substitui usuario atual e notifica listeners', () {
      final p = AuthProvider();
      int notifications = 0;
      p.addListener(() => notifications++);

      final novoUsuario = Usuario.fromJson(_usuarioJson(id: 99, nome: 'Novo Nome'));
      p.updateUsuario(novoUsuario);

      expect(p.usuario?.id, 99);
      expect(p.usuario?.nome, 'Novo Nome');
      expect(notifications, 1);
    });
  });
}
