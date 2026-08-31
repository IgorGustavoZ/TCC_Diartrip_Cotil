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

  /// Igual ao PUT /grupos/{id} do backend (`GrupoAtualizarInput`): o
  /// orçamento total não é mais editável diretamente aqui — ele é sempre a
  /// soma dos orçamentos individuais (ver [alterarMeuOrcamento]).
  static Future<void> atualizar({
    required int id,
    required String nomeGrupo,
    required String destinoPrincipal,
    required String dataInicio,
    required String dataFim,
    required String tipoViagem,
    required String preferencias,
  }) async {
    final r = await dio.put('/grupos/$id', data: {
      'nome_grupo': nomeGrupo,
      'destino_principal': destinoPrincipal,
      'data_inicio': dataInicio,
      'data_fim': dataFim,
      'tipo_viagem': tipoViagem,
      'preferencias': preferencias,
    });
    _check(r);
  }

  static Future<void> deletar(int id) async {
    final r = await dio.delete('/grupos/$id');
    _check(r);
  }

  static Future<void> sair(int idGrupo) async {
    final r = await dio.delete('/grupos/$idGrupo/sair');
    _check(r);
  }

  static Future<void> alterarMeuOrcamento(int idGrupo, double orcamento) async {
    final r = await dio.patch('/grupos/$idGrupo/meu-orcamento', data: {'orcamento': orcamento});
    _check(r);
  }

  static Future<void> publicar(int idGrupo, {required bool publica, int? limiteParticipantes}) async {
    final r = await dio.put('/grupos/$idGrupo/publicar', data: {
      'publica': publica,
      if (limiteParticipantes != null) 'limite_participantes': limiteParticipantes,
    });
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
