import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:diartrip_flutter/screens/auth/login_screen.dart';
import 'package:diartrip_flutter/core/theme.dart';
import 'package:diartrip_flutter/providers/auth_provider.dart';
import 'package:diartrip_flutter/providers/language_provider.dart';
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
      home: MultiProvider(
        providers: [
          ChangeNotifierProvider<AuthProvider>.value(value: auth),
          ChangeNotifierProvider<LanguageProvider>(create: (_) => LanguageProvider()),
        ],
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

    testWidgets('exibe subtítulo Planejamento de Viagens com IA', (tester) async {
      await pumpApp(tester);
      expect(find.text('Planejamento de Viagens com IA'), findsOneWidget);
    });

    testWidgets('exibe dois campos de formulário', (tester) async {
      await pumpApp(tester);
      expect(find.byType(TextFormField), findsNWidgets(2));
    });

    testWidgets('exibe botão Entrar', (tester) async {
      await pumpApp(tester);
      expect(find.text('Entrar'), findsWidgets);
    });

    testWidgets('exibe link Cadastrar-se', (tester) async {
      await pumpApp(tester);
      expect(find.text('Cadastrar-se'), findsOneWidget);
    });

    testWidgets('logo do Diartrip (favicon) visível', (tester) async {
      await pumpApp(tester);
      final logo = tester.widget<Image>(find.byType(Image));
      expect((logo.image as AssetImage).assetName, 'assets/images/favicon-diartrip.png');
    });
  });

  group('LoginScreen — validação de formulário', () {
    testWidgets('exibe erro quando email inválido ao submeter', (tester) async {
      await pumpApp(tester);
      await tester.enterText(find.byType(TextFormField).first, 'emailinvalido');
      await tester.tap(find.text('Entrar').last);
      await tester.pump();
      expect(find.text('E-mail inválido'), findsOneWidget);
    });

    testWidgets('exibe erro quando senha vazia ao submeter', (tester) async {
      await pumpApp(tester);
      await tester.enterText(find.byType(TextFormField).first, 'a@b.com');
      await tester.tap(find.text('Entrar').last);
      await tester.pump();
      expect(find.text('Digite a senha'), findsOneWidget);
    });

    testWidgets('não exibe erro com campos válidos', (tester) async {
      final auth = FakeAuthProvider();
      await pumpApp(tester, provider: auth);
      await tester.enterText(find.byType(TextFormField).first, 'a@b.com');
      await tester.enterText(find.byType(TextFormField).last, 'SenhaQualquer');
      await tester.tap(find.text('Entrar').last);
      await tester.pumpAndSettle();
      expect(find.text('E-mail inválido'), findsNothing);
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

    testWidgets('exibe texto Entrar quando não está carregando', (tester) async {
      await pumpApp(tester);
      expect(find.text('Entrar'), findsWidgets);
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
      await tester.tap(find.text('Entrar').last);
      await tester.pumpAndSettle();

      expect(find.textContaining('Credenciais'), findsOneWidget);
    });
  });

  group('LoginScreen — navegação', () {
    testWidgets('toque em Cadastrar-se navega para /register', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.text('Cadastrar-se'));
      await tester.pumpAndSettle();
      expect(find.text('Register'), findsOneWidget);
    });
  });
}
