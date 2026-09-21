import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:diartrip_flutter/core/theme.dart';
import 'package:diartrip_flutter/widgets/collapsible_section.dart';

Widget _app({bool aberta = false}) => MaterialApp(
      theme: AppTheme.dark,
      home: Scaffold(
        body: SingleChildScrollView(
          child: CollapsibleSection(
            icon: Icons.history,
            title: 'Viagens passadas',
            count: 3,
            initiallyExpanded: aberta,
            child: const Text('conteudo-da-secao'),
          ),
        ),
      ),
    );

void main() {
  group('CollapsibleSection', () {
    testWidgets('começa recolhida: mostra só o cabeçalho e o contador', (tester) async {
      await tester.pumpWidget(_app());
      expect(find.text('Viagens passadas'), findsOneWidget);
      expect(find.text('3'), findsOneWidget);
      expect(find.text('conteudo-da-secao'), findsNothing);
    });

    testWidgets('toque no cabeçalho abre e mostra o conteúdo', (tester) async {
      await tester.pumpWidget(_app());
      await tester.tap(find.text('Viagens passadas'));
      await tester.pumpAndSettle();
      expect(find.text('conteudo-da-secao'), findsOneWidget);
    });

    testWidgets('segundo toque recolhe de novo', (tester) async {
      await tester.pumpWidget(_app());
      await tester.tap(find.text('Viagens passadas'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Viagens passadas'));
      await tester.pumpAndSettle();
      expect(find.text('conteudo-da-secao'), findsNothing);
    });

    testWidgets('initiallyExpanded abre já no início', (tester) async {
      await tester.pumpWidget(_app(aberta: true));
      expect(find.text('conteudo-da-secao'), findsOneWidget);
    });

    group('rolagem automática ao abrir', () {
      // Página longa: 1200px de conteúdo antes da seção e 1500px depois, para
      // haver espaço de rolagem dos dois lados (viewport padrão do teste: 600px).
      Widget pagina(ScrollController c) => MaterialApp(
            theme: AppTheme.dark,
            home: Scaffold(
              body: SingleChildScrollView(
                controller: c,
                child: Column(
                  children: [
                    const SizedBox(height: 1200),
                    const CollapsibleSection(
                      icon: Icons.history,
                      title: 'Viagens passadas',
                      count: 3,
                      child: SizedBox(height: 900, child: Text('conteudo-da-secao')),
                    ),
                    const SizedBox(height: 1500),
                  ],
                ),
              ),
            ),
          );

      testWidgets('ao abrir, leva a seção para o topo da tela', (tester) async {
        final c = ScrollController();
        addTearDown(c.dispose);
        await tester.pumpWidget(pagina(c));
        c.jumpTo(800); // cabeçalho aparece perto do fim da tela (y ≈ 400)
        await tester.pump();
        final antes = c.offset;
        expect(tester.getTopLeft(find.byType(CollapsibleSection)).dy, greaterThan(300));

        await tester.tap(find.text('Viagens passadas'));
        await tester.pumpAndSettle();

        expect(c.offset, greaterThan(antes)); // rolou para baixo sozinho
        expect(tester.getTopLeft(find.byType(CollapsibleSection)).dy, closeTo(0, 1));
        expect(find.text('conteudo-da-secao'), findsOneWidget);
      });

      testWidgets('ao recolher, não move a página', (tester) async {
        final c = ScrollController();
        addTearDown(c.dispose);
        await tester.pumpWidget(pagina(c));
        c.jumpTo(800);
        await tester.pump();
        await tester.tap(find.text('Viagens passadas'));
        await tester.pumpAndSettle();
        final aberto = c.offset;

        await tester.tap(find.text('Viagens passadas'));
        await tester.pumpAndSettle();

        expect(c.offset, aberto);
        expect(find.text('conteudo-da-secao'), findsNothing);
      });

      testWidgets('funciona também fora de uma área rolável', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            theme: AppTheme.dark,
            home: const Scaffold(
              body: Align(
                alignment: Alignment.topCenter,
                child: CollapsibleSection(
                  icon: Icons.history,
                  title: 'Viagens passadas',
                  child: Text('conteudo-da-secao'),
                ),
              ),
            ),
          ),
        );
        await tester.tap(find.text('Viagens passadas'));
        await tester.pumpAndSettle();
        expect(find.text('conteudo-da-secao'), findsOneWidget);
        expect(tester.takeException(), isNull);
      });
    });

    testWidgets('ícone é opcional: sem ele, só título, contador e seta', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.dark,
          home: const Scaffold(
            body: CollapsibleSection(
              title: 'Viagens passadas',
              count: 3,
              child: Text('conteudo-da-secao'),
            ),
          ),
        ),
      );
      expect(find.byIcon(Icons.history), findsNothing);
      expect(find.text('Viagens passadas'), findsOneWidget);
      expect(find.byIcon(Icons.keyboard_arrow_down), findsOneWidget);
    });

    testWidgets('a seta gira ao abrir (puxador visível o tempo todo)', (tester) async {
      await tester.pumpWidget(_app());
      expect(find.byIcon(Icons.keyboard_arrow_down), findsOneWidget);
      AnimatedRotation rot() => tester.widget<AnimatedRotation>(find.byType(AnimatedRotation));
      expect(rot().turns, 0);
      await tester.tap(find.text('Viagens passadas'));
      await tester.pumpAndSettle();
      expect(rot().turns, 0.5);
    });
  });
}
