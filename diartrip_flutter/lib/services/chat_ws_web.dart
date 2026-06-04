// Implementação web: o navegador inclui cookies automaticamente.
import 'package:web_socket_channel/web_socket_channel.dart';

WebSocketChannel connectWs(Uri uri, Map<String, dynamic> headers) =>
    WebSocketChannel.connect(uri);
