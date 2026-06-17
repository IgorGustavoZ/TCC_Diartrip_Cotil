// Implementação nativa (Android, iOS, Windows, macOS, Linux).
// Injeta Cookie e X-CSRF-Token no handshake WebSocket.
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

WebSocketChannel connectWs(Uri uri, Map<String, dynamic> headers) =>
    IOWebSocketChannel.connect(uri, headers: headers);
