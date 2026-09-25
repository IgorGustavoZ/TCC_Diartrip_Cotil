// TEMPORÁRIO — diagnóstico do "pumpAndSettle timed out" de viagem_passada_test.dart
// que só acontece no CI (Linux). Não faz nenhuma verificação que possa falhar:
// só imprime linhas "DIAG ..." dizendo o que fica animando/pendente. Apagar
// este arquivo depois que a causa for encontrada.
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

void _d(String m) => debugPrint('DIAG $m');

void main() {
  late Dio d;

  setUpAll(() {
    d = Dio(BaseOptions(baseUrl: 'http://api.test', validateStatus: (s) => s != null && s < 500))
      ..transformer = SyncTransformer();
    final a = DioAdapter(dio: d);
    a.onGet('/grupos/2', (s) => s.reply(200, {
          'id_grupo': 2,
          'nome_grupo': 'Viagem 2',
          'destino_principal': 'Paris, França',
          'data_inicio': '2099-01-01',
          'data_fim': '2099-01-10',
          'orcamento': 1000,
          'criador_id': 7,
          'codigo_convite': 'ABC123',
        }));
    a.onGet('/grupos/2/membros', (s) => s.reply(200, [
          {'id_usuario': 7, 'nome': 'K', 'foto_perfil': null, 'cargo': 'admin'},
        ]));
    a.onGet('/grupos/2/dashboard', (s) => s.reply(200, {
          'geral': {
            'orcamento_total': 1000,
            'total_consumido': 50,
            'orcamento_restante': 950,
            'percentual_consumido': 5,
            'distribuicao_categorias': [],
          },
          'pessoal': {
            'total_pago_por_mim': 50,
            'minha_divida_atual': 0,
            'ultimos_gastos_pessoais': [],
          },
        }));
    api.dio = d;
  });

  testWidgets('DIAG: requisição direta do Dio com mock completa em tempo falso?', (tester) async {
    var done = false;
    Object? erro;
    d.get('/grupos/2').then((_) => done = true, onError: (e) => erro = e);
    for (var i = 1; i <= 5; i++) {
      await tester.pump(const Duration(milliseconds: 100));
      _d('dio direto: apos ${i * 100}ms done=$done erro=$erro');
    }
  });

  testWidgets('DIAG: o que fica animando na ViagemScreen', (tester) async {
    tester.view.physicalSize = const Size(1080, 3600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final auth = FakeAuthProvider()..setUsuario(const Usuario(id: 7, nome: 'K'));
    await tester.pumpWidget(MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthProvider>.value(value: auth),
        ChangeNotifierProvider<LanguageProvider>(create: (_) => LanguageProvider()),
      ],
      child: MaterialApp(theme: AppTheme.dark, home: const ViagemScreen(idGrupo: 2, initialTab: 'geral')),
    ));

    for (final ms in [0, 100, 100, 100, 300, 500, 1000, 2000, 5000]) {
      await tester.pump(Duration(milliseconds: ms));
      _d('tela: +${ms}ms spinners=${find.byType(CircularProgressIndicator).evaluate().length} '
          'titulo="Viagem 2"=${find.text('Viagem 2').evaluate().length} '
          'callbacksTransitorios=${tester.binding.transientCallbackCount} '
          'frameAgendado=${tester.binding.hasScheduledFrame}');
    }

    final linhas = WidgetsBinding.instance.rootElement!
        .toStringDeep()
        .split('\n')
        .where((l) => RegExp(r'ticker active|CircularProgressIndicator|LinearProgressIndicator|(forward|reverse|repeat)\b').hasMatch(l))
        .take(25);
    for (final l in linhas) {
      _d('widget: ${l.trim()}');
    }
  });
}
