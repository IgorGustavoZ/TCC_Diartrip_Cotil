import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../../core/app_logger.dart';
import '../../../core/theme.dart';
import '../../../models/grupo.dart';
import '../../../models/mensagem.dart';
import '../../../services/chat_service.dart';

class ChatTab extends StatefulWidget {
  final int idGrupo;
  final int meId;
  final List<Membro> membros;

  const ChatTab({
    super.key,
    required this.idGrupo,
    required this.meId,
    required this.membros,
  });

  @override
  State<ChatTab> createState() => _ChatTabState();
}

class _ChatTabState extends State<ChatTab> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  final List<Mensagem> _msgs = [];
  int _lastId = 0;

  final _msgCtrl = TextEditingController();
  final _scroll = ScrollController();
  WebSocketChannel? _ws;
  bool _sending = false;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    _loadMsgs();
    _connectWs();
  }

  @override
  void dispose() {
    _ws?.sink.close();
    _pollTimer?.cancel();
    _msgCtrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _loadMsgs() async {
    try {
      final novas =
          await ChatService.listar(widget.idGrupo, sinceId: _lastId);
      if (!mounted || novas.isEmpty) return;
      setState(() {
        _msgs.addAll(novas);
        _lastId = novas.last.id;
      });
      _scrollBottom();
    } catch (e, s) {
      AppLogger.captureError('ChatTab._loadMsgs', e, s);
    }
  }

  Future<void> _connectWs() async {
    try {
      _ws = await ChatService.conectarWs(widget.idGrupo);
      _ws!.stream.listen(
        _onWsData,
        onError: (e) {
          AppLogger.warning('ChatTab._connectWs', 'WS error: $e — iniciando polling');
          _startPolling();
        },
        onDone: _startPolling,
      );
    } catch (e, s) {
      AppLogger.captureError('ChatTab._connectWs', e, s);
      _startPolling();
    }
  }

  void _onWsData(dynamic raw) {
    try {
      final map = raw is String
          ? jsonDecode(raw) as Map<String, dynamic>
          : raw as Map<String, dynamic>;
      if (map.containsKey('erro')) return;
      final msg = Mensagem.fromJson(map);
      if (_msgs.any((m) => m.id == msg.id)) return;
      if (mounted) {
        setState(() {
          _msgs.add(msg);
          if (msg.id > _lastId) _lastId = msg.id;
        });
        _scrollBottom();
      }
    } catch (e) {
      AppLogger.warning('ChatTab._onWsData', 'JSON inválido: $e');
    }
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(
      const Duration(seconds: 3),
      (_) => _loadMsgs(),
    );
  }

  Future<void> _send() async {
    final texto = _msgCtrl.text.trim();
    if (texto.isEmpty || _sending) return;
    _msgCtrl.clear();
    setState(() => _sending = true);
    try {
      final nova = await ChatService.enviar(widget.idGrupo, texto);
      if (mounted) {
        setState(() {
          if (!_msgs.any((m) => m.id == nova.id)) {
            _msgs.add(nova);
            if (nova.id > _lastId) _lastId = nova.id;
          }
        });
        _scrollBottom();
      }
    } catch (e, s) {
      AppLogger.captureError('ChatTab._send', e, s);
    }
    if (mounted) setState(() => _sending = false);
  }

  void _scrollBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            controller: _scroll,
            padding: const EdgeInsets.all(12),
            itemCount: _msgs.length,
            itemBuilder: (_, i) {
              final m = _msgs[i];
              final isMe = m.idUsuario == widget.meId;
              return Align(
                alignment:
                    isMe ? Alignment.centerRight : Alignment.centerLeft,
                child: Container(
                  margin: const EdgeInsets.symmetric(vertical: 3),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 8),
                  constraints: BoxConstraints(
                      maxWidth:
                          MediaQuery.of(context).size.width * 0.75),
                  decoration: BoxDecoration(
                    color: isMe
                        ? AppTheme.primary
                        : AppTheme.surfaceVariant,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: isMe
                        ? CrossAxisAlignment.end
                        : CrossAxisAlignment.start,
                    children: [
                      if (!isMe)
                        Text(m.nome,
                            style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                fontSize: 11,
                                color: AppTheme.accent)),
                      Text(m.conteudo,
                          style: const TextStyle(
                              fontSize: 14, color: Colors.white)),
                      Text(
                        _fmt(m.dataEnvio),
                        style: const TextStyle(
                            fontSize: 10,
                            color: AppTheme.onSurfaceMuted),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(10),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _msgCtrl,
                  decoration:
                      const InputDecoration(hintText: 'Message...'),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                onPressed: _sending ? null : _send,
                icon: const Icon(Icons.send_rounded),
              ),
            ],
          ),
        ),
      ],
    );
  }

  String _fmt(String iso) {
    try {
      return DateFormat('HH:mm').format(DateTime.parse(iso).toLocal());
    } catch (_) {
      return '';
    }
  }
}
