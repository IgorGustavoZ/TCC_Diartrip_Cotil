import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/roteiro.dart';

class RoteiroService {
  static Future<List<Roteiro>> listar(int idGrupo) async {
    final r = await dio.get('/grupos/$idGrupo/roteiros');
    _check(r);
    return (r.data as List).map((e) => Roteiro.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<void> criar({
    required int idGrupo,
    required String titulo,
    required String descricao,
  }) async {
    final r = await dio.post('/roteiros', data: {
      'id_grupo': idGrupo,
      'titulo': titulo,
      'descricao': descricao,
    });
    _check(r);
  }

  static Future<void> atualizar({
    required int id,
    required String titulo,
    required String descricao,
  }) async {
    final r = await dio.put('/roteiros/$id', data: {
      'titulo': titulo,
      'descricao': descricao,
    });
    _check(r);
  }

  static Future<void> deletar(int id) async {
    final r = await dio.delete('/roteiros/$id');
    _check(r);
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro ${r.statusCode}');
    }
  }
}
