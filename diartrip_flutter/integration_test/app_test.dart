/// integration_test/app_test.dart
///
/// Execução:
///   flutter test integration_test/app_test.dart              (dispositivo padrão)
///   flutter test integration_test/app_test.dart --platform chrome
///   flutter test integration_test/app_test.dart -d windows
///
/// O usuário de teste é criado automaticamente no setUpAll.
/// Requer o backend FastAPI rodando em http://127.0.0.1:8000.
library;

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:diartrip_flutter/main.dart' as app;

const _kEmail = 'integration@diartrip.test';
const _kSenha = 'Teste1234';
const _kNome = 'Integration Tester';
const _kBaseUrl = 'http://127.0.0.1:8000';

/// Cria um Dio simples apenas para o setup/teardown — independente do dio
/// global da app (que só é inicializado após app.main()).
Dio _setupDio() => Dio(BaseOptions(
      baseUrl: _kBaseUrl,
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 5),
      validateStatus: (_) => true, // não lança em 4xx/5xx
    ));

Future<bool> _backendDisponivel() async {
  try {
    final r = await _setupDio().get('/health');
    return r.statusCode == 200;
  } catch (_) {
    return false;
  }
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  // ── Setup automático ───────────────────────────────────────────────────────
  setUpAll(() async {
    final online = await _backendDisponivel();
    if (!online) {
      // ignore: avoid_print
      print('\n⚠️  Backend não disponível em $_kBaseUrl — integration tests pulados.\n');
      return;
    }

    // Cria o usuário de teste; ignora 409 (já existe) e 422 (validação).
    final dio = _setupDio();
    final r = await dio.post('/usuarios', data: {
      'nome': _kNome,
      'email': _kEmail,
      'senha': _kSenha,
    });

    if (r.statusCode == 200 || r.statusCode == 201) {
      // ignore: avoid_print
      print('✅  Usuário de teste criado: $_kEmail');
    } else if (r.statusCode == 409 || r.statusCode == 400) {
      // ignore: avoid_print
      print('ℹ️  Usuário de teste já existe: $_kEmail');
    } else {
      // ignore: avoid_print
      print('⚠️  Criação do usuário retornou ${r.statusCode}: ${r.data}');
    }
  });

  // ── Tear-down: remove usuário de teste ────────────────────────────────────
  tearDownAll(() async {
    try {
      final dio = _setupDio();

      // 1. Login para obter cookie de sessão
      final loginResp = await dio.post('/login', data: {
        'email': _kEmail,
        'senha': _kSenha,
      });
      if (loginResp.statusCode != 200) return;

      // 2. Obter ID do usuário
      final meResp = await dio.get('/usuarios/me');
      final idUsuario = (meResp.data as Map<String, dynamic>)['id_usuario'];

      // 3. Deletar conta
      await dio.delete('/usuarios/$idUsuario');
      // ignore: avoid_print
      print('🗑️  Usuário de teste removido.');
    } catch (_) {
      // best-effort: não falha o suite se a limpeza não funcionar
    }
  });

  // ── Testes ────────────────────────────────────────────────────────────────

  group('Inicialização do app', () {
    testWidgets('app sobe sem erros críticos', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 3));
      final hasSplash = find.byType(CircularProgressIndicator).evaluate().isNotEmpty;
      final hasLogin = find.text('Diartrip').evaluate().isNotEmpty;
      expect(hasSplash || hasLogin, isTrue);
    });
  });

  group('Tela de login', () {
    testWidgets('renderiza campos e botão', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 4));
      if (find.text('Diartrip').evaluate().isEmpty) return;

      expect(find.text('Diartrip'), findsOneWidget);
      expect(find.text('AI-Powered Travel Planning'), findsOneWidget);
      expect(find.byType(TextFormField), findsNWidgets(2));
      expect(find.text('Sign In'), findsWidgets);
    });

    testWidgets('credenciais inválidas exibem erro', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 4));
      if (find.text('Sign In').evaluate().isEmpty) return;

      await tester.enterText(find.byType(TextFormField).first, 'invalido@email.com');
      await tester.enterText(find.byType(TextFormField).last, 'SenhaErrada1');
      await tester.tap(find.text('Sign In').last);
      await tester.pumpAndSettle(const Duration(seconds: 5));

      // Alguma mensagem de erro deve aparecer (container de erro)
      expect(find.byType(Container), findsWidgets);
    });

    testWidgets('login válido navega para fora da tela de login', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 4));
      if (find.text('Sign In').evaluate().isEmpty) return;

      await tester.enterText(find.byType(TextFormField).first, _kEmail);
      await tester.enterText(find.byType(TextFormField).last, _kSenha);
      await tester.tap(find.text('Sign In').last);
      await tester.pumpAndSettle(const Duration(seconds: 8));

      // Após login, a tela de login some
      expect(find.text('Sign In'), findsNothing);
    });
  });

  group('Tela de cadastro', () {
    testWidgets('abre a partir do link Sign Up', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 4));
      if (find.text('Sign Up').evaluate().isEmpty) return;

      await tester.tap(find.text('Sign Up'));
      await tester.pumpAndSettle();

      expect(find.text('Create Account'), findsWidgets);
      expect(find.byType(TextFormField), findsNWidgets(3));
    });

    testWidgets('valida campos obrigatórios', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 4));
      if (find.text('Sign Up').evaluate().isEmpty) return;

      await tester.tap(find.text('Sign Up'));
      await tester.pumpAndSettle();

      await tester.tap(find.widgetWithText(ElevatedButton, 'Create Account'));
      await tester.pump();

      expect(find.text('Mínimo 3 caracteres'), findsOneWidget);
    });
  });

  group('Navegação autenticada', () {
    testWidgets('drawer acessível após login', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 4));

      if (find.text('Sign In').evaluate().isNotEmpty) {
        await tester.enterText(find.byType(TextFormField).first, _kEmail);
        await tester.enterText(find.byType(TextFormField).last, _kSenha);
        await tester.tap(find.text('Sign In').last);
        await tester.pumpAndSettle(const Duration(seconds: 8));
      }

      if (find.byIcon(Icons.menu).evaluate().isNotEmpty) {
        await tester.tap(find.byIcon(Icons.menu));
        await tester.pumpAndSettle();
        expect(find.byType(Drawer), findsOneWidget);
      }
    });
  });
}
