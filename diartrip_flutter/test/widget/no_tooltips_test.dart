import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:diartrip_flutter/main.dart';
import 'package:diartrip_flutter/providers/auth_provider.dart';
import 'package:diartrip_flutter/providers/language_provider.dart';
import 'helpers/fake_auth_provider.dart';

const _dica = 'Assistente de Viagem IA';

Widget _appComBotao({required bool semTooltips}) => MaterialApp(
      builder: semTooltips
          ? (context, child) =>
              TooltipVisibility(visible: false, child: child ?? const SizedBox.shrink())
          : null,
      home: Scaffold(
        appBar: AppBar(
          actions: [
            IconButton(
              icon: const Icon(Icons.smart_toy_outlined),
              tooltip: _dica,
              onPressed: () {},
            ),
          ],
        ),
      ),
    );

Future<void> _passarMouseNoBotao(WidgetTester tester) async {
  final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
  await mouse.addPointer(location: Offset.zero);
  addTearDown(mouse.removePointer);
  await mouse.moveTo(tester.getCenter(find.byIcon(Icons.smart_toy_outlined)));
  await tester.pump(const Duration(seconds: 2));
}

void main() {
  testWidgets('controle: sem o TooltipVisibility o balão aparece ao passar o mouse', (tester) async {
    await tester.pumpWidget(_appComBotao(semTooltips: false));
    await _passarMouseNoBotao(tester);
    expect(find.text(_dica), findsOneWidget);
  });

  testWidgets('com o TooltipVisibility o balão não aparece', (tester) async {
    await tester.pumpWidget(_appComBotao(semTooltips: true));
    await _passarMouseNoBotao(tester);
    expect(find.text(_dica), findsNothing);
  });

  testWidgets('o DiartripApp real roda com os tooltips desligados', (tester) async {
    tester.view.physicalSize = const Size(1080, 1920);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<AuthProvider>.value(value: FakeAuthProvider()),
          ChangeNotifierProvider<LanguageProvider>(create: (_) => LanguageProvider()),
        ],
        child: const DiartripApp(),
      ),
    );
    // Splash -> tryAutoLogin (fake, sem rede) -> /login
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    // Uma tela qualquer do app (aqui, o login) enxerga tooltips desligados.
    final contexto = tester.element(find.byType(Scaffold).first);
    expect(TooltipVisibility.of(contexto), isFalse);
  });
}
