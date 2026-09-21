import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http_mock_adapter/http_mock_adapter.dart';
import 'package:provider/provider.dart';

import 'package:diartrip_flutter/core/api_client.dart' as api;
import 'package:diartrip_flutter/core/theme.dart';
import 'package:diartrip_flutter/models/usuario.dart';
import 'package:diartrip_flutter/providers/auth_provider.dart';
import 'package:diartrip_flutter/providers/language_provider.dart';
import 'package:diartrip_flutter/screens/grupo/viagem_screen.dart';
import 'helpers/fake_auth_provider.dart';

/// Viagens que já passaram viram só consulta: este teste monta a ViagemScreen
/// inteira com a API simulada e compara, aba por aba, uma viagem PASSADA (id 1)
/// com uma FUTURA (id 2) — a futura tem que continuar exatamente como sempre.
const _passada = 1;
const _futura = 2;

final _lang = LanguageProvider();
String _t(String key) => _lang.translate(key);

void _registrar(DioAdapter a, int id, String inicio, String fim) {
  a.onGet('/grupos/$id', (s) => s.reply(200, {
        'id_grupo': id,
        'nome_grupo': 'Viagem $id',
        'destino_principal': 'Paris, França',
        'data_inicio': inicio,
        'data_fim': fim,
        'orcamento': 1000,
        'tipo_viagem': 'cultural',
        'preferencias': 'museus',
        'criador_id': 7,
        'codigo_convite': 'ABC123',
        'publica': false,
        'vagas_ocupadas': 1,
      }));
  a.onGet('/grupos/$id/membros', (s) => s.reply(200, [
        {'id_usuario': 7, 'nome': 'Kaneki Ken', 'foto_perfil': null, 'cargo': 'admin'},
      ]));
  a.onGet('/grupos/$id/dashboard', (s) => s.reply(200, {
        'geral': {
          'orcamento_total': 1000,
          'total_consumido': 50,
          'orcamento_restante': 950,
          'percentual_consumido': 5,
          'distribuicao_categorias': [
            {'categoria': 'Alimentação', 'total': 50},
          ],
        },
        'pessoal': {
          'total_pago_por_mim': 50,
          'minha_divida_atual': 0,
          'ultimos_gastos_pessoais': [],
          'meu_orcamento': 1000,
          'disponivel': 950,
        },
        'admin': {
          'ranking_contribuicao_financeira': [
            {'nome': 'Kaneki Ken', 'total': 50},
          ],
          'estatisticas': {'membros_ativos': 1, 'total_fotos_subidas': 0, 'itens_no_roteiro': 1},
        },
      }));
  a.onGet('/grupos/$id/gastos', (s) => s.reply(200, [
        {
          'id_gasto': 1,
          'id_grupo': id,
          'id_usuario': 7,
          'nome': 'Kaneki Ken',
          'valor': 50.0,
          'categoria': 'Alimentação',
          'descricao': 'Almoço',
          'data_gasto': inicio,
        },
      ]));
  a.onGet('/grupos/$id/roteiros', (s) => s.reply(200, [
        {'id_roteiro': 1, 'id_grupo': id, 'titulo': 'Dia 1 - Museu', 'descricao': 'Louvre', 'origem_ia': false},
      ]));
  a.onGet('/grupos/$id/solicitacoes', (s) => s.reply(200, []));
}

Future<void> _abrir(WidgetTester tester, int id, String aba) async {
  tester.view.physicalSize = const Size(1080, 3600);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);

  final auth = FakeAuthProvider()..setUsuario(const Usuario(id: 7, nome: 'Kaneki Ken'));
  await tester.pumpWidget(
    MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthProvider>.value(value: auth),
        ChangeNotifierProvider<LanguageProvider>(create: (_) => LanguageProvider()),
      ],
      child: MaterialApp(
        theme: AppTheme.dark,
        home: ViagemScreen(idGrupo: id, initialTab: aba),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  setUpAll(() {
    final d = Dio(BaseOptions(baseUrl: 'http://api.test', validateStatus: (s) => s != null && s < 500))
      ..transformer = SyncTransformer();
    final adapter = DioAdapter(dio: d);
    _registrar(adapter, _passada, '2020-01-01', '2020-01-10');
    _registrar(adapter, _futura, '2099-01-01', '2099-01-10');
    api.dio = d;
  });

  group('cabeçalho da viagem', () {
    testWidgets('futura: mostra o botão de copiar código de convite', (tester) async {
      await _abrir(tester, _futura, 'geral');
      expect(find.text(_t('viagem.copyCode')), findsOneWidget);
    });

    testWidgets('passada: sem o código de convite', (tester) async {
      await _abrir(tester, _passada, 'geral');
      expect(find.text(_t('viagem.copyCode')), findsNothing);
      // ...mas a viagem em si continua aparecendo normalmente
      expect(find.text('Viagem $_passada'), findsWidgets);
    });
  });

  group('Visão Geral — completa nos dois casos', () {
    for (final id in [_passada, _futura]) {
      testWidgets('viagem $id: dashboard, orçamento e categorias', (tester) async {
        await _abrir(tester, id, 'geral');
        expect(find.textContaining(_t('viagem.dashboard')), findsOneWidget);
        expect(find.text(_t('viagem.budgetTotal')), findsOneWidget);
        expect(find.text(_t('overview.totalSpent')), findsOneWidget);
        expect(find.textContaining('Alimentação'), findsWidgets);
      });
    }
  });

  group('Minhas Finanças', () {
    testWidgets('futura: tem "Alterar orçamento"', (tester) async {
      await _abrir(tester, _futura, 'pessoal');
      expect(find.text(_t('finances.editBudget')), findsOneWidget);
    });

    testWidgets('passada: sem "Alterar orçamento", mas o orçamento continua visível', (tester) async {
      await _abrir(tester, _passada, 'pessoal');
      expect(find.text(_t('finances.editBudget')), findsNothing);
      expect(find.textContaining(_t('finances.myBudget').toUpperCase()), findsOneWidget); // DashboardCard exibe o título em maiúsculas
      expect(find.text('R\$ 1000.00'), findsWidgets);
    });
  });

  group('Admin', () {
    testWidgets('futura: tem Explorar Viagens e Solicitações', (tester) async {
      await _abrir(tester, _futura, 'admin');
      expect(find.text(_t('viagem.explore.panel')), findsOneWidget);
      expect(find.text(_t('viagem.explore.requests')), findsOneWidget);
    });

    testWidgets('passada: sem Explorar Viagens nem Solicitações; membros e estatísticas ficam', (tester) async {
      await _abrir(tester, _passada, 'admin');
      expect(find.text(_t('viagem.explore.panel')), findsNothing);
      expect(find.text(_t('viagem.explore.requests')), findsNothing);
      expect(find.text(_t('admin.manageMembers')), findsOneWidget);
      expect(find.textContaining(_t('admin.ranking').toUpperCase()), findsOneWidget);
      expect(find.textContaining(_t('admin.statistics').toUpperCase()), findsOneWidget);
    });
  });

  group('Gastos', () {
    testWidgets('futura: formulário de registro + editar/excluir no histórico', (tester) async {
      await _abrir(tester, _futura, 'gastos');
      expect(find.textContaining(_t('viagem.registerExpense')), findsWidgets);
      expect(find.byIcon(Icons.edit_outlined), findsOneWidget);
      expect(find.byIcon(Icons.delete_outline), findsOneWidget);
    });

    testWidgets('passada: só o histórico, sem registrar/editar/excluir', (tester) async {
      await _abrir(tester, _passada, 'gastos');
      expect(find.textContaining(_t('viagem.registerExpense')), findsNothing);
      expect(find.text(_t('viagem.history')), findsOneWidget);
      expect(find.text('Almoço'), findsOneWidget); // o gasto continua listado
      expect(find.byIcon(Icons.edit_outlined), findsNothing);
      expect(find.byIcon(Icons.delete_outline), findsNothing);
    });
  });

  group('Roteiro', () {
    testWidgets('futura (admin): gerar por IA, adicionar, editar e excluir', (tester) async {
      await _abrir(tester, _futura, 'roteiro');
      expect(find.text(_t('viagem.itinerary.ia.regenerateBtn')), findsOneWidget);
      expect(find.byType(FloatingActionButton), findsOneWidget);
      expect(find.byIcon(Icons.edit_outlined), findsOneWidget);
      expect(find.byIcon(Icons.delete_outline), findsOneWidget);
    });

    testWidgets('passada: só consulta — sem gerar, adicionar, editar nem excluir', (tester) async {
      await _abrir(tester, _passada, 'roteiro');
      expect(find.text('Dia 1 - Museu'), findsOneWidget); // o roteiro continua visível
      expect(find.text(_t('viagem.itinerary.ia.regenerateBtn')), findsNothing);
      expect(find.text(_t('viagem.itinerary.ia.createBtn')), findsNothing);
      expect(find.byType(FloatingActionButton), findsNothing);
      expect(find.byIcon(Icons.edit_outlined), findsNothing);
      expect(find.byIcon(Icons.delete_outline), findsNothing);
    });
  });

  group('Info', () {
    testWidgets('futura: código de convite e configurações editáveis', (tester) async {
      await _abrir(tester, _futura, 'info');
      expect(find.text(_t('info.inviteCode')), findsOneWidget);
      expect(find.text('ABC123'), findsWidgets);
      expect(find.text(_t('viagem.settings.save')), findsOneWidget);
      final campos = tester.widgetList<TextField>(find.byType(TextField));
      expect(campos, isNotEmpty);
      expect(campos.every((c) => c.enabled != false), isTrue);
    });

    testWidgets('passada: sem código de convite e configurações travadas', (tester) async {
      await _abrir(tester, _passada, 'info');
      expect(find.text(_t('info.inviteCode')), findsNothing);
      expect(find.text('ABC123'), findsNothing);
      // configurações continuam à vista, porém sem edição
      expect(find.textContaining(_t('viagem.settings.title')), findsOneWidget);
      expect(find.text(_t('viagem.pastReadOnly')), findsOneWidget);
      expect(find.text(_t('viagem.settings.save')), findsNothing);
      final campos = tester.widgetList<TextField>(find.byType(TextField));
      expect(campos, isNotEmpty);
      expect(campos.every((c) => c.enabled == false), isTrue);
      // o destino continua sendo mostrado
      expect(find.text('Paris, França'), findsWidgets);
    });
  });
}
