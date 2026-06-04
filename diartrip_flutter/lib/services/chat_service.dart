import 'package:dio/dio.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../core/api_client.dart';
import '../core/constants.dart';
import '../models/mensagem.dart';
// Importação condicional: usa implementação nativa em mobile/desktop e web no browser.
import 'chat_ws_web.dart' if (dart.library.io) 'chat_ws_native.dart';

class ChatService {
  static Future<List<Mensagem>> listar(int idGrupo, {int? sinceId}) async {
    final r = await dio.get(
      '/grupos/$idGrupo/chat',
      queryParameters: sinceId != null ? {'since_id': sinceId} : null,
    );
    _check(r);
    return (r.data as List)
        .map((e) => Mensagem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  static Future<Mensagem> enviar(int idGrupo, String conteudo) async {
    final r = await dio.post('/grupos/$idGrupo/chat', data: {'conteudo': conteudo});
    _check(r);
    return Mensagem.fromJson(r.data as Map<String, dynamic>);
  }

  /// Conecta via WebSocket com cookies da sessão.
  /// Web: o browser envia cookies automaticamente.
  /// Nativo: injeta Cookie + X-CSRF-Token no header de upgrade.
  static Future<WebSocketChannel> conectarWs(int idGrupo) async {
    final uri = Uri.parse('${Constants.wsBaseUrl}/grupos/$idGrupo/chat/ws');
    final cookieHeader = await buildCookieHeader();
    final csrf = await getCsrfToken();
    return connectWs(uri, {
      if (cookieHeader.isNotEmpty) 'Cookie': cookieHeader,
      if (csrf != null) 'X-CSRF-Token': csrf,
    });
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro ${r.statusCode}');
    }
  }
}
