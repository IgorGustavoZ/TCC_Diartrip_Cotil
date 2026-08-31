import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../../core/app_logger.dart';
import '../../../providers/language_provider.dart';
import '../../../core/web_style.dart';
import '../../../models/grupo.dart';
import '../../../models/mensagem.dart';
import '../../../services/chat_service.dart';
import '../../../widgets/avatar_widget.dart';

/// Aba "chat" de viagem.html: chat do grupo — igual a
/// `conectarChatWS()`/`_renderMsgHtml()`. No Flutter Web usa polling a cada
/// 3s direto (o websocket já causou travamentos da aplicação inteira nessa
/// plataforma); em desktop/mobile nativo ainda tenta websocket primeiro,
/// caindo pro mesmo polling se a conexão falhar ou nunca resolver.
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
    if (kIsWeb) {
      // No Flutter Web, tentar abrir o websocket aqui já travou a aplicação
      // inteira ao entrar nesta aba — em vez de arriscar de novo, usamos
      // direto o polling (o mesmo fallback que já existia para quando o
      // websocket falha), garantindo um chat funcional sem esse risco.
      _startPolling();
      return;
    }
    try {
      // Defesa extra: se a conexão nunca resolver (nem sucesso, nem erro),
      // cai no polling depois de um tempo em vez de ficar esperando pra
      // sempre — outra forma como isso poderia travar a experiência do chat.
      _ws = await ChatService.conectarWs(widget.idGrupo).timeout(const Duration(seconds: 8));
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

  Membro? _membroDe(int idUsuario) {
    for (final m in widget.membros) {
      if (m.id == idUsuario) return m;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final lang = context.watch<LanguageProvider>();
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
      child: GlassContainer(
        child: Column(
          children: [
            Expanded(
              child: _msgs.isEmpty
                  ? const SizedBox.shrink()
                  : ListView.builder(
                      controller: _scroll,
                      padding: const EdgeInsets.all(14),
                      itemCount: _msgs.length,
                      itemBuilder: (_, i) {
                        final m = _msgs[i];
                        final isMe = m.idUsuario == widget.meId;
                        final membro = _membroDe(m.idUsuario);
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            mainAxisAlignment: isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (!isMe) ...[
                                AvatarWidget(
                                  fotoUrl: membro?.fotoPerfil,
                                  iniciais: m.nome.isNotEmpty ? m.nome[0].toUpperCase() : '?',
                                  radius: 16,
                                ),
                                const SizedBox(width: 8),
                              ],
                              Flexible(
                                child: Column(
                                  crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
                                  children: [
                                    Padding(
                                      padding: const EdgeInsets.symmetric(horizontal: 4),
                                      child: Text('${m.nome} · ${_fmt(m.dataEnvio)}',
                                          style: const TextStyle(fontSize: 11, color: WebColors.textMuted)),
                                    ),
                                    const SizedBox(height: 3),
                                    Container(
                                      constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.7),
                                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                      decoration: BoxDecoration(
                                        gradient: isMe ? WebColors.gradient : null,
                                        color: isMe ? null : WebColors.surface2,
                                        borderRadius: BorderRadius.circular(14).copyWith(
                                          bottomRight: isMe ? const Radius.circular(4) : null,
                                          bottomLeft: !isMe ? const Radius.circular(4) : null,
                                        ),
                                      ),
                                      child: Text(m.conteudo,
                                          style: TextStyle(fontSize: 14, color: isMe ? Colors.white : WebColors.text)),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      height: 44,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: WebColors.surface2,
                        borderRadius: BorderRadius.circular(WebColors.radiusPill),
                        border: Border.all(color: WebColors.border),
                      ),
                      child: TextField(
                        controller: _msgCtrl,
                        style: const TextStyle(color: WebColors.text, fontSize: 14),
                        decoration: InputDecoration(
                          filled: false,
                          border: InputBorder.none,
                          enabledBorder: InputBorder.none,
                          focusedBorder: InputBorder.none,
                          isCollapsed: true,
                          hintText: lang.translate('viagem.chatPlaceholder'),
                          hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 14),
                        ),
                        onSubmitted: (_) => _send(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  GradientButton(
                    radius: WebColors.radiusPill,
                    padding: const EdgeInsets.all(12),
                    onPressed: _sending ? null : _send,
                    child: const Icon(Icons.send_rounded, size: 20),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
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
