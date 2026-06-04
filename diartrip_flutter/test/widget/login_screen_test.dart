import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:diartrip_flutter/screens/auth/login_screen.dart';
import 'package:diartrip_flutter/core/theme.dart';
import 'package:diartrip_flutter/providers/auth_provider.dart';
import 'helpers/fake_auth_provider.dart';

// Define viewport 1080×1920 (tamanho comum de celular) para evitar overflow
// nos testes de widget com ConstrainedBox(maxWidth: 400).
Future<void> pumpApp(
  WidgetTester tester, {
  FakeAuthProvider? provider,
}) async {
  tester.view.physicalSize = const Size(1080, 1920);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);

  final auth = provider ?? FakeAuthProvider();
  await tester.pumpWidget(
    MaterialApp(
      theme: AppTheme.dark,
      home: ChangeNotifierProvider<AuthProvider>.value(
        value: auth,
        child: const LoginScreen(),
      ),
      routes: {
        '/lobby': (_) => const Scaffold(body: Text('Lobby')),
        '/register': (_) => const Scaffold(body: Text('Register')),
      },
    ),
  );
}

void main() {
  group('LoginScreen — renderização', () {
    testWidgets('exibe título Diartrip', (tester) async {
      await pumpApp(tester);
      expect(find.text('Diartrip'), findsOneWidget);
    });

    testWidgets('exibe subtítulo AI-Powered Travel Planning', (tester) async {
      await pumpApp(tester);
      expect(find.text('AI-Powered Travel Planning'), findsOneWidget);
    });

    testWidgets('exibe dois campos de formulário', (tester) async {
      await pumpApp(tester);
      expect(find.byType(TextFormField), findsNWidgets(2));
    });

    testWidgets('exibe botão Sign In', (tester) async {
      await pumpApp(tester);
      expect(find.text('Sign In'), findsWidgets);
    });

    testWidgets('exibe link Sign Up', (tester) async {
      await pumpApp(tester);
      expect(find.text('Sign Up'), findsOneWidget);
    });

    testWidgets('ícone de avião visível', (tester) async {
      await pumpApp(tester);
      expect(find.byIcon(Icons.flight_takeoff), findsOneWidget);
    });
  });

  group('LoginScreen — validação de formulário', () {
    testWidgets('exibe erro quando email inválido ao submeter', (tester) async {
      await pumpApp(tester);
      await tester.enterText(find.byType(TextFormField).first, 'emailinvalido');
      await tester.tap(find.text('Sign In').last);
      await tester.pump();
      expect(find.text('Email inválido'), findsOneWidget);
    });

    testWidgets('exibe erro quando senha vazia ao submeter', (tester) async {
      await pumpApp(tester);
      await tester.enterText(find.byType(TextFormField).first, 'a@b.com');
      await tester.tap(find.text('Sign In').last);
      await tester.pump();
      expect(find.text('Digite a senha'), findsOneWidget);
    });

    testWidgets('não exibe erro com campos válidos', (tester) async {
      final auth = FakeAuthProvider();
      await pumpApp(tester, provider: auth);
      await tester.enterText(find.byType(TextFormField).first, 'a@b.com');
      await tester.enterText(find.byType(TextFormField).last, 'SenhaQualquer');
      await tester.tap(find.text('Sign In').last);
      await tester.pumpAndSettle();
      expect(find.text('Email inválido'), findsNothing);
      expect(find.text('Digite a senha'), findsNothing);
    });
  });

  group('LoginScreen — estados de loading', () {
    testWidgets('botão desabilitado durante loading', (tester) async {
      final auth = FakeAuthProvider();
      await pumpApp(tester, provider: auth);
      auth.setLoading(true);
      await tester.pump();
      final btn = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
      expect(btn.onPressed, isNull);
    });

    testWidgets('exibe CircularProgressIndicator durante loading', (tester) async {
      final auth = FakeAuthProvider();
      await pumpApp(tester, provider: auth);
      auth.setLoading(true);
      await tester.pump();
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('exibe texto Sign In quando não está carregando', (tester) async {
      await pumpApp(tester);
      expect(find.text('Sign In'), findsWidgets);
      expect(find.byType(CircularProgressIndicator), findsNothing);
    });
  });

  group('LoginScreen — toggle de senha', () {
    testWidgets('campo de senha começa oculto (ícone visibility)', (tester) async {
      await pumpApp(tester);
      expect(find.byIcon(Icons.visibility), findsOneWidget);
      expect(find.byIcon(Icons.visibility_off), findsNothing);
    });

    testWidgets('tap no ícone alterna para visibility_off', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.byIcon(Icons.visibility));
      await tester.pump();
      expect(find.byIcon(Icons.visibility_off), findsOneWidget);
    });
  });

  group('LoginScreen — mensagem de erro', () {
    testWidgets('exibe mensagem quando login falha', (tester) async {
      final auth = FakeAuthProvider();
      auth.loginError = Exception('Credenciais inválidas');
      await pumpApp(tester, provider: auth);

      await tester.enterText(find.byType(TextFormField).first, 'a@b.com');
      await tester.enterText(find.byType(TextFormField).last, 'Errado123');
      await tester.tap(find.text('Sign In').last);
      await tester.pumpAndSettle();

      expect(find.textContaining('Credenciais'), findsOneWidget);
    });
  });

  group('LoginScreen — navegação', () {
    testWidgets('toque em Sign Up navega para /register', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.text('Sign Up'));
      await tester.pumpAndSettle();
      expect(find.text('Register'), findsOneWidget);
    });
  });
}
