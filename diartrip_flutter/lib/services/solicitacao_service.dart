import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/solicitacao.dart';

/// Pedidos de participação recebidos por um grupo publicado em Explorar
/// Viagens — mesmos endpoints usados por `viagem.html` (painel Admin).
class SolicitacaoService {
  static Future<List<Solicitacao>> listar(int idGrupo) async {
    final r = await dio.get('/grupos/$idGrupo/solicitacoes');
    _check(r);
    return (r.data as List).map((e) => Solicitacao.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<void> aceitar(int idSolicitacao) async {
    final r = await dio.put('/solicitacoes/$idSolicitacao/aceitar');
    _check(r);
  }

  static Future<void> recusar(int idSolicitacao) async {
    final r = await dio.put('/solicitacoes/$idSolicitacao/recusar');
    _check(r);
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro ${r.statusCode}');
    }
  }
}
