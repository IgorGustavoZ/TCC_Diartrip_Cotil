import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/viagem_explorar.dart';

/// Mirrors GET/POST /explorar used by backend/frontend/lobby-pags/explorar-viagens.html.
class ExplorarViagensService {
  static Future<List<ViagemExplorar>> listar({String? destino}) async {
    final r = await dio.get(
      '/explorar',
      queryParameters: (destino != null && destino.isNotEmpty) ? {'destino': destino} : null,
    );
    _check(r);
    return (r.data as List).map((e) => ViagemExplorar.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<void> solicitar(int idGrupo, {String? mensagem, double? orcamento}) async {
    final r = await dio.post('/explorar/$idGrupo/solicitar', data: {
      'mensagem': mensagem,
      'orcamento': orcamento,
    });
    _check(r);
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw ApiException(apiError(r.data, 'Erro ${r.statusCode}'), r.statusCode);
    }
  }
}
