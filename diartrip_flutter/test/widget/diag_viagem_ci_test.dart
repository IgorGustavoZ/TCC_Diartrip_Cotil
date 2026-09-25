// TEMPORÁRIO — diagnóstico do "pumpAndSettle timed out" de viagem_passada_test.dart
// que só acontece no CI (Linux): a requisição do Dio com mock não completa em
// tempo falso. Este arquivo não faz nenhuma verificação que possa falhar: só
// imprime linhas "DIAG ..." dizendo em que etapa a requisição para.
// Apagar este arquivo depois que a causa for encontrada.
import 'dart:io' show Platform;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http_mock_adapter/http_mock_adapter.dart';

void _d(String m) => debugPrint('DIAG $m');

/// Só repassa para o adaptador de mock, registrando quando entra e sai.
class _Espiao implements HttpClientAdapter {
  final HttpClientAdapter inner;
  _Espiao(this.inner);

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? s, Future<void>? c) async {
    _d('  adaptador.fetch: ENTROU');
    final r = await inner.fetch(o, s, c);
    _d('  adaptador.fetch: SAIU (status ${r.statusCode})');
    return r;
  }

  @override
  void close({bool force = false}) => inner.close(force: force);
}

Dio _novoDio({Transformer? transformer}) {
  final d = Dio(BaseOptions(baseUrl: 'http://api.test', validateStatus: (s) => s != null && s < 500));
  if (transformer != null) d.transformer = transformer;
  final a = DioAdapter(dio: d);
  a.onGet('/x', (s) => s.reply(200, {'ok': true}));
  d.httpClientAdapter = _Espiao(a);
  d.interceptors.add(InterceptorsWrapper(
    onRequest: (o, h) {
      _d('  interceptor.onRequest');
      h.next(o);
    },
    onResponse: (r, h) {
      _d('  interceptor.onResponse');
      h.next(r);
    },
    onError: (e, h) {
      _d('  interceptor.onError ${e.type} ${e.message}');
      h.next(e);
    },
  ));
  return d;
}

Future<void> _tentar(WidgetTester tester, String nome, Dio d) async {
  _d('--- $nome');
  var done = false;
  Object? erro;
  d.get('/x').then((_) {
    done = true;
    _d('  get() COMPLETOU');
  }, onError: (e) {
    erro = e;
    _d('  get() ERRO $e');
  });
  for (var i = 1; i <= 3; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
  _d('  resultado apos 300ms falsos: done=$done erro=$erro');
}

void main() {
  testWidgets('DIAG ambiente', (tester) async {
    _d('so=${Platform.operatingSystem} dart=${Platform.version.split(' ').first}');
    _d('adaptador padrao do Dio: ${Dio().httpClientAdapter.runtimeType}');
    _d('transformer padrao do Dio: ${Dio().transformer.runtimeType}');
  });

  testWidgets('DIAG 1: SyncTransformer (como o teste da viagem)', (tester) async {
    await _tentar(tester, 'SyncTransformer', _novoDio(transformer: SyncTransformer()));
  });

  testWidgets('DIAG 2: transformer padrao do Dio', (tester) async {
    await _tentar(tester, 'transformer padrao', _novoDio());
  });

  testWidgets('DIAG 3: mesma requisicao dentro de runAsync (loop de eventos real)', (tester) async {
    final d = _novoDio(transformer: SyncTransformer());
    _d('--- runAsync');
    final r = await tester.runAsync(() => d.get('/x').timeout(const Duration(seconds: 5)));
    _d('  runAsync completou: status=${r?.statusCode}');
  });
}
