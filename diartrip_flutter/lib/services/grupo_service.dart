import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/grupo.dart';

class GrupoService {
  static Future<List<Grupo>> listar() async {
    final r = await dio.get('/grupos');
    _check(r);
    return (r.data as List).map((e) => Grupo.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<List<Grupo>> buscar(String query) async {
    final r = await dio.get('/grupos/buscar', queryParameters: {'nome': query});
    _check(r);
    return (r.data as List).map((e) => Grupo.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<Grupo> get(int id) async {
    final r = await dio.get('/grupos/$id');
    _check(r);
    return Grupo.fromJson(r.data as Map<String, dynamic>);
  }

  // Backend retorna {"mensagem", "id_grupo", "codigo_convite"} — não o Grupo completo.
  static Future<int> criar({
    required String nomeGrupo,
    required String destinoPrincipal,
    required String dataInicio,
    required String dataFim,
    required double orcamento,
    required String tipoViagem,
    String preferencias = '',
  }) async {
    final r = await dio.post('/grupos', data: {
      'nome_grupo': nomeGrupo,
      'destino_principal': destinoPrincipal,
      'data_inicio': dataInicio,
      'data_fim': dataFim,
      'orcamento': orcamento,
      'tipo_viagem': tipoViagem,
      'preferencias': preferencias,
    });
    _check(r);
    return (r.data as Map<String, dynamic>)['id_grupo'] as int;
  }

  static Future<void> entrar(String codigoConvite) async {
    final r = await dio.post('/grupos/entrar', data: {'codigo_convite': codigoConvite});
    _check(r);
  }

  // Backend retorna {"mensagem":"Grupo atualizado"} — sem objeto completo.
  // Chamar GrupoService.get(id) após atualizar se precisar dos dados atualizados.
  // TODOS os campos são obrigatórios no backend (GrupoInput) — o PUT é substituição total.
  static Future<void> atualizar({
    required int id,
    required String nomeGrupo,
    required String destinoPrincipal,
    required String dataInicio,
    required String dataFim,
    required double orcamento,
    required String tipoViagem,
    required String preferencias,
  }) async {
    final r = await dio.put('/grupos/$id', data: {
      'nome_grupo': nomeGrupo,
      'destino_principal': destinoPrincipal,
      'data_inicio': dataInicio,
      'data_fim': dataFim,
      'orcamento': orcamento,
      'tipo_viagem': tipoViagem,
      'preferencias': preferencias,
    });
    _check(r);
  }

  static Future<void> deletar(int id) async {
    final r = await dio.delete('/grupos/$id');
    _check(r);
  }

  static Future<List<Membro>> listarMembros(int idGrupo) async {
    final r = await dio.get('/grupos/$idGrupo/membros');
    _check(r);
    return (r.data as List).map((e) => Membro.fromJson(e as Map<String, dynamic>)).toList();
  }

  static Future<void> promover(int idGrupo, int idUsuario) async {
    final r = await dio.put('/grupos/$idGrupo/membros/$idUsuario/promover');
    _check(r);
  }

  static Future<void> rebaixar(int idGrupo, int idUsuario) async {
    final r = await dio.put('/grupos/$idGrupo/membros/$idUsuario/rebaixar');
    _check(r);
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro ${r.statusCode}');
    }
  }
}
