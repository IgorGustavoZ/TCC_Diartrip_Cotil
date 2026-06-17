import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/gasto.dart';

class GastoService {
  static Future<List<Gasto>> listar(int idGrupo) async {
    final r = await dio.get('/grupos/$idGrupo/gastos');
    _check(r);
    return (r.data as List).map((e) => Gasto.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<void> criar({
    required int idGrupo,
    required double valor,
    required String categoria,
    String? descricao,
    String? dataGasto,
    List<int>? idUsuariosDivisao,
  }) async {
    final r = await dio.post('/grupos/$idGrupo/gastos', data: {
      'valor': valor,
      'categoria': categoria,
      if (descricao != null && descricao.isNotEmpty) 'descricao': descricao,
      if (dataGasto != null) 'data_gasto': dataGasto,
      if (idUsuariosDivisao != null && idUsuariosDivisao.isNotEmpty)
        'id_usuarios_divisao': idUsuariosDivisao,
    });
    _check(r);
  }

  // GastoUpdate no backend exige: valor (float), categoria (str), descricao (str obrigatório).
  // data_gasto não existe em GastoUpdate — NÃO enviar.
  static Future<void> atualizar({
    required int idGasto,
    required double valor,
    required String categoria,
    String? descricao,
  }) async {
    final r = await dio.put('/gastos/$idGasto', data: {
      'valor': valor,
      'categoria': categoria,
      'descricao': descricao ?? '',   // obrigatório no backend — nunca omitir
    });
    _check(r);
  }

  static Future<void> deletar(int idGasto) async {
    final r = await dio.delete('/gastos/$idGasto');
    _check(r);
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro ${r.statusCode}');
    }
  }
}
