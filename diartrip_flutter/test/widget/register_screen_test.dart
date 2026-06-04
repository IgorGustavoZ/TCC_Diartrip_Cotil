import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:diartrip_flutter/screens/auth/register_screen.dart';
import 'package:diartrip_flutter/core/theme.dart';
import 'package:diartrip_flutter/providers/auth_provider.dart';
import 'helpers/fake_auth_provider.dart';

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
        child: const RegisterScreen(),
      ),
      routes: {
        '/lobby': (_) => const Scaffold(body: Text('Lobby')),
        '/login': (_) => const Scaffold(body: Text('Login')),
      },
    ),
  );
}

void main() {
  group('RegisterScreen — renderização', () {
    testWidgets('exibe título Create Account', (tester) async {
      await pumpApp(tester);
      expect(find.text('Create Account'), findsWidgets);
    });

    testWidgets('exibe três campos de formulário', (tester) async {
      await pumpApp(tester);
      expect(find.byType(TextFormField), findsNWidgets(3));
    });

    testWidgets('exibe botão Create Account', (tester) async {
      await pumpApp(tester);
      expect(find.widgetWithText(ElevatedButton, 'Create Account'), findsOneWidget);
    });

    testWidgets('exibe link Sign In', (tester) async {
      await pumpApp(tester);
      expect(find.text('Sign In'), findsOneWidget);
    });

    testWidgets('ícone de avião presente', (tester) async {
      await pumpApp(tester);
      expect(find.byIcon(Icons.flight_takeoff), findsOneWidget);
    });
  });

  group('RegisterScreen — validação', () {
    testWidgets('erro quando nome muito curto', (tester) async {
      await pumpApp(tester);
      await tester.enterText(find.byType(TextFormField).at(0), 'ab');
      await tester.tap(find.widgetWithText(ElevatedButton, 'Create Account'));
      await tester.pump();
      expect(find.text('Mínimo 3 caracteres'), findsOneWidget);
    });

    testWidgets('erro quando email inválido', (tester) async {
      await pumpApp(tester);
      await tester.enterText(find.byType(TextFormField).at(0), 'Nome Válido');
      await tester.enterText(find.byType(TextFormField).at(1), 'emailsemarroba');
      await tester.tap(find.widgetWithText(ElevatedButton, 'Create Account'));
      await tester.pump();
      expect(find.text('Email inválido'), findsOneWidget);
    });

    testWidgets('erro quando senha muito curta', (tester) async {
      await pumpApp(tester);
      await tester.enterText(find.byType(TextFormField).at(0), 'Nome Válido');
      await tester.enterText(find.byType(TextFormField).at(1), 'a@b.com');
      await tester.enterText(find.byType(TextFormField).at(2), '1234567');
      await tester.tap(find.widgetWithText(ElevatedButton, 'Create Account'));
      await tester.pump();
      expect(find.text('Mínimo 8 caracteres'), findsOneWidget);
    });

    testWidgets('erro quando senha sem letra maiúscula', (tester) async {
      await pumpApp(tester);
      await tester.enterText(find.byType(TextFormField).at(0), 'Nome Válido');
      await tester.enterText(find.byType(TextFormField).at(1), 'a@b.com');
      await tester.enterText(find.byType(TextFormField).at(2), 'semmaius1');
      await tester.tap(find.widgetWithText(ElevatedButton, 'Create Account'));
      await tester.pump();
      expect(find.text('Precisa de uma maiúscula'), findsOneWidget);
    });

    testWidgets('erro quando senha sem número', (tester) async {
      await pumpApp(tester);
      await tester.enterText(find.byType(TextFormField).at(0), 'Nome Válido');
      await tester.enterText(find.byType(TextFormField).at(1), 'a@b.com');
      await tester.enterText(find.byType(TextFormField).at(2), 'SemNumeroAqui');
      await tester.tap(find.widgetWithText(ElevatedButton, 'Create Account'));
      await tester.pump();
      expect(find.text('Precisa de um número'), findsOneWidget);
    });

    testWidgets('sem erros com todos os campos válidos', (tester) async {
      final auth = FakeAuthProvider();
      await pumpApp(tester, provider: auth);
      await tester.enterText(find.byType(TextFormField).at(0), 'Nome Completo');
      await tester.enterText(find.byType(TextFormField).at(1), 'valido@email.com');
      await tester.enterText(find.byType(TextFormField).at(2), 'Senha1234');
      await tester.tap(find.widgetWithText(ElevatedButton, 'Create Account'));
      await tester.pump();
      expect(find.text('Mínimo 3 caracteres'), findsNothing);
      expect(find.text('Email inválido'), findsNothing);
      expect(find.text('Mínimo 8 caracteres'), findsNothing);
    });
  });

  group('RegisterScreen — toggle de senha', () {
    testWidgets('senha começa oculta (ícone visibility visível)', (tester) async {
      await pumpApp(tester);
      expect(find.byIcon(Icons.visibility), findsOneWidget);
      expect(find.byIcon(Icons.visibility_off), findsNothing);
    });

    testWidgets('tap no ícone alterna visibilidade da senha', (tester) async {
      await pumpApp(tester);
      await tester.tap(find.byIcon(Icons.visibility));
      await tester.pump();
      expect(find.byIcon(Icons.visibility_off), findsOneWidget);
    });
  });

  group('RegisterScreen — loading', () {
    // RegisterScreen gerencia _loading como estado local (não via AuthProvider),
    // então os testes de loading verificam o estado padrão e erro de submissão.
    testWidgets('botão habilitado no estado inicial', (tester) async {
      await pumpApp(tester);
      final btn = tester.widget<ElevatedButton>(
        find.widgetWithText(ElevatedButton, 'Create Account'),
      );
      expect(btn.onPressed, isNotNull);
    });

    testWidgets('não exibe CircularProgressIndicator no estado inicial', (tester) async {
      await pumpApp(tester);
      expect(find.byType(CircularProgressIndicator), findsNothing);
    });
  });
}
