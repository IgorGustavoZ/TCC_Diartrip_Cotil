import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:diartrip_flutter/core/theme.dart';
import 'package:diartrip_flutter/providers/language_provider.dart';
import 'package:diartrip_flutter/screens/grupo/form_viagem_manual_screen.dart';
import 'package:diartrip_flutter/screens/grupo/form_viagem_screen.dart';

Future<void> _pump(WidgetTester tester, Widget home) async {
  tester.view.physicalSize = const Size(1080, 2400);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    ChangeNotifierProvider<LanguageProvider>(
      create: (_) => LanguageProvider(),
      child: MaterialApp(
        theme: AppTheme.dark,
        home: home,
        routes: {
          '/nova-viagem': (_) => const FormViagemScreen(),
          '/nova-viagem/manual': (_) => const FormViagemManualScreen(),
        },
      ),
    ),
  );
}

void main() {
  group('montarPreferenciasViagem', () {
    test('vazio quando nada foi informado', () {
      expect(montarPreferenciasViagem(), '');
    });

    test('usa os rótulos em português que o backend reconhece', () {
      expect(
        montarPreferenciasViagem(participantes: '4', transporte: 'Avião', preferencias: 'museus'),
        'Participantes: 4 | Transporte: Avião | museus',
      );
    });

    test('ignora campos em branco e apara espaços', () {
      expect(
        montarPreferenciasViagem(participantes: '  ', transporte: ' carro ', preferencias: ''),
        'Transporte: carro',
      );
    });

    test('limita a 1000 caracteres', () {
      expect(montarPreferenciasViagem(preferencias: 'a' * 1500).length, 1000);
    });
  });

  group('FormViagemManualScreen', () {
    testWidgets('mostra todos os campos do formulário', (tester) async {
      await _pump(tester, const FormViagemManualScreen());
      expect(find.text('Nome da viagem'), findsOneWidget);
      expect(find.text('Cidade'), findsOneWidget);
      expect(find.text('Data de início'), findsOneWidget);
      expect(find.text('Data de fim'), findsOneWidget);
      expect(find.text('Seu orçamento (R\$)'), findsOneWidget);
      expect(find.text('Tipo de viagem'), findsOneWidget);
      expect(find.text('Gastronômico'), findsOneWidget);
      expect(find.text('Criar viagem'), findsOneWidget);
      expect(find.byType(TextField), findsNWidgets(6));
    });

    testWidgets('enviar vazio mostra "preencha todos os campos" e não cria nada', (tester) async {
      await _pump(tester, const FormViagemManualScreen());
      await tester.ensureVisible(find.text('Criar viagem'));
      await tester.tap(find.text('Criar viagem'));
      await tester.pump();
      expect(find.text('Preencha todos os campos obrigatórios.'), findsOneWidget);
    });

    testWidgets('sem escolher o tipo de viagem ainda pede para preencher', (tester) async {
      await _pump(tester, const FormViagemManualScreen());
      await tester.enterText(find.byType(TextField).at(0), 'Europa');
      await tester.enterText(find.byType(TextField).at(1), 'Paris');
      await tester.ensureVisible(find.text('Criar viagem'));
      await tester.tap(find.text('Criar viagem'));
      await tester.pump();
      expect(find.text('Preencha todos os campos obrigatórios.'), findsOneWidget);
    });

    testWidgets('escolher o tipo de viagem marca o chip', (tester) async {
      await _pump(tester, const FormViagemManualScreen());
      await tester.tap(find.text('Aventura'));
      await tester.pump();
      final chip = tester.widget<ChoiceChip>(find.widgetWithText(ChoiceChip, 'Aventura'));
      expect(chip.selected, isTrue);
      final outro = tester.widget<ChoiceChip>(find.widgetWithText(ChoiceChip, 'Cultural'));
      expect(outro.selected, isFalse);
    });

    // Preenche nome, cidade, as duas datas (pelo seletor real) e o tipo.
    Future<void> preencherAteOTipo(WidgetTester tester) async {
      await tester.enterText(find.byType(TextField).at(0), 'Europa Verão');
      await tester.enterText(find.byType(TextField).at(1), 'Paris');
      for (final _ in [0, 1]) {
        // 1ª volta: início (hoje); 2ª volta: fim (o seletor já abre em início+1).
        await tester.tap(find.text('aaaa-mm-dd').first);
        await tester.pumpAndSettle();
        await tester.tap(find.text('OK'));
        await tester.pumpAndSettle();
      }
      await tester.tap(find.text('Cultural'));
      await tester.pump();
    }

    testWidgets('datas escolhidas aparecem nos campos (fim sempre depois do início)', (tester) async {
      await _pump(tester, const FormViagemManualScreen());
      await preencherAteOTipo(tester);
      expect(find.text('aaaa-mm-dd'), findsNothing); // as duas datas foram preenchidas
    });

    testWidgets('orçamento inválido mostra o erro de orçamento', (tester) async {
      await _pump(tester, const FormViagemManualScreen());
      await preencherAteOTipo(tester);
      await tester.enterText(find.byType(TextField).at(2), 'abc');
      await tester.ensureVisible(find.text('Criar viagem'));
      await tester.tap(find.text('Criar viagem'));
      await tester.pump();
      expect(find.text('Informe um orçamento válido (ex: 3000.00).'), findsOneWidget);
    });

    testWidgets('formulário válido chama a criação; se falhar, mostra o erro e destrava o botão', (tester) async {
      await _pump(tester, const FormViagemManualScreen());
      await preencherAteOTipo(tester);
      await tester.enterText(find.byType(TextField).at(2), '3000,50');
      await tester.ensureVisible(find.text('Criar viagem'));
      await tester.tap(find.text('Criar viagem'));
      await tester.pumpAndSettle();
      // No teste não há API (dio não inicializado): a criação falha e a tela
      // volta ao normal em vez de travar em "carregando".
      expect(find.textContaining('Erro ao criar viagem.'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsNothing);
      expect(find.text('Criar viagem'), findsOneWidget);
    });

    testWidgets('botão "Usar o assistente" leva ao assistente em chat', (tester) async {
      await _pump(tester, const FormViagemManualScreen());
      await tester.tap(find.text('Usar o assistente'));
      await tester.pumpAndSettle();
      expect(find.byType(FormViagemScreen), findsOneWidget);
      expect(find.byType(FormViagemManualScreen), findsNothing);
    });
  });

  group('FormViagemScreen (assistente) → opção manual', () {
    testWidgets('mostra o botão "Preencher manualmente"', (tester) async {
      await _pump(tester, const FormViagemScreen());
      expect(find.text('Preencher manualmente'), findsOneWidget);
    });

    testWidgets('tocar em "Preencher manualmente" abre o formulário', (tester) async {
      await _pump(tester, const FormViagemScreen());
      await tester.tap(find.text('Preencher manualmente'));
      await tester.pumpAndSettle();
      expect(find.byType(FormViagemManualScreen), findsOneWidget);
      expect(find.byType(FormViagemScreen), findsNothing);
    });
  });

  test('novas traduções existem em português e inglês', () {
    const chaves = [
      'formViagem.manualTitle', 'formViagem.manualHeader', 'formViagem.manualHint',
      'formViagem.manualBtn', 'formViagem.assistantHint', 'formViagem.assistantBtn',
      'formViagem.optional', 'formViagem.fillAll', 'formViagem.invalidInfo', 'formViagem.submit',
    ];
    for (final idioma in ['pt', 'en']) {
      for (final k in chaves) {
        expect(LanguageProvider.translations[idioma]![k], isNotNull, reason: '$idioma / $k');
      }
    }
  });
}
