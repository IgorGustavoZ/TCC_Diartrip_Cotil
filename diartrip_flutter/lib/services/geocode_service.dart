import '../core/api_client.dart';

/// Proxy do autocomplete de cidade (Geoapify) — igual ao usado em
/// chat-viagem.html: a chave da API fica só no backend.
class GeocodeService {
  static Future<List<String>> autocomplete(String texto) async {
    try {
      final r = await dio.get('/geocode/autocomplete', queryParameters: {'text': texto});
      if (r.statusCode == null || r.statusCode! >= 400) return [];
      final features = (r.data as Map<String, dynamic>)['features'] as List? ?? [];
      return features
          .map((f) => ((f as Map<String, dynamic>)['properties'] as Map<String, dynamic>?)?['formatted'] as String?)
          .whereType<String>()
          .toList();
    } catch (_) {
      // Sugestões são best-effort: falha de rede não deve travar o wizard.
      return [];
    }
  }
}
