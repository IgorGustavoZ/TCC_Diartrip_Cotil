import '../core/api_client.dart';

class IaService {
  static Future<String> perguntar({
    required String pergunta,
    required int idGrupo,
  }) async {
    final r = await dio.post('/chat', data: {
      'pergunta': pergunta,
      'id_grupo': idGrupo,
    });
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro na IA');
    }
    return (r.data as Map<String, dynamic>)['resposta'] as String? ?? '';
  }
}
