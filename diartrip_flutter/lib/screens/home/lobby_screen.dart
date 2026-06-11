import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import '../../core/app_logger.dart';
import '../../core/theme.dart';
import '../../models/grupo.dart';
import '../../providers/auth_provider.dart';
import '../../services/grupo_service.dart';
import '../../services/ia_service.dart';
import '../../widgets/app_drawer.dart';
import '../../widgets/avatar_widget.dart';
import '../../widgets/trip_card.dart';

class LobbyScreen extends StatefulWidget {
  const LobbyScreen({super.key});
  @override
  State<LobbyScreen> createState() => _LobbyScreenState();
}

class _LobbyScreenState extends State<LobbyScreen> {
  List<Grupo> _grupos = [];
  bool _loading = true;

  // Chat IA
  final List<_Msg> _msgs = [];
  final _chatCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  Grupo? _grupoSelecionado;
  bool _iaLoading = false;

  @override
  void initState() {
    super.initState();
    _loadGrupos();
  }

  @override
  void dispose() {
    _chatCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadGrupos() async {
    try {
      final g = await GrupoService.listar();
      if (mounted) setState(() { _grupos = g; _loading = false; });
    } catch (e, s) {
      AppLogger.captureError('LobbyScreen._loadGrupos', e, s);
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _enviarPergunta() async {
    final texto = _chatCtrl.text.trim();
    if (texto.isEmpty || _grupoSelecionado == null || _iaLoading) return;
    _chatCtrl.clear();
    setState(() {
      _msgs.add(_Msg(texto, true));
      _iaLoading = true;
    });
    _scrollDown();
    try {
      final resp = await IaService.perguntar(
        pergunta: texto,
        idGrupo: _grupoSelecionado!.id,
      );
      if (mounted) setState(() => _msgs.add(_Msg(resp, false)));
    } catch (e) {
      if (mounted) setState(() => _msgs.add(_Msg('Erro: $e', false)));
    } finally {
      if (mounted) setState(() => _iaLoading = false);
      _scrollDown();
    }
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showChatBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => StatefulBuilder(
        builder: (ctx, setModalState) => SizedBox(
          height: MediaQuery.of(context).size.height * 0.85,
          child: _chatPanel(),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().usuario;
    final isWide = MediaQuery.of(context).size.width > 800;

    return Scaffold(
      appBar: AppBar(
        title: Text('Hello, ${user?.nome.split(' ').first ?? ''}! 👋'),
        actions: [
          // AI chat acessível via ícone no AppBar em mobile
          if (!isWide)
            IconButton(
              icon: const Icon(Icons.smart_toy_outlined, color: AppTheme.accent),
              tooltip: 'AI Assistant',
              onPressed: () => _showChatBottomSheet(context),
            ),
          AvatarWidget(
            fotoUrl: user?.fotoPerfil,
            iniciais: user?.iniciais ?? '?',
            radius: 16,
            onTap: () => Navigator.pushNamed(context, '/perfil/${user?.id}'),
          ),
          const SizedBox(width: 16),
        ],
      ),
      drawer: const AppDrawer(activeRoute: '/lobby'),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.pushNamed(context, '/nova-viagem'),
        icon: const Icon(Icons.add),
        label: const Text('New Trip'),
      ),
      body: isWide
          ? Row(children: [
              Expanded(child: _tripsList()),   // Expanded aqui, não dentro de _tripsList
              const VerticalDivider(width: 1),
              Expanded(child: _chatPanel()),
            ])
          : _tripsList(),   // corpo do Scaffold recebe widget normal, não Expanded
    );
  }

  Widget _tripsList() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_grupos.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.luggage_outlined, size: 64, color: AppTheme.onSurfaceMuted),
            const SizedBox(height: 12),
            const Text('No trips yet', style: TextStyle(color: AppTheme.onSurfaceMuted)),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () => Navigator.pushNamed(context, '/nova-viagem'),
              icon: const Icon(Icons.add, size: 16),
              label: const Text('Create your first trip'),
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _loadGrupos,
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _grupos.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (ctx, i) => TripCard(
          grupo: _grupos[i],
          onTap: () {
            setState(() => _grupoSelecionado = _grupos[i]);
            Navigator.pushNamed(ctx, '/viagem/${_grupos[i].id}');
          },
        ),
      ),
    );
  }

  Widget _chatPanel() {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          color: AppTheme.surface,
          child: Row(
            children: [
              const Icon(Icons.smart_toy_outlined, color: AppTheme.primary, size: 20),
              const SizedBox(width: 8),
              const Text('AI Travel Assistant', style: TextStyle(fontWeight: FontWeight.w600)),
              const Spacer(),
              if (_grupoSelecionado != null)
                Chip(
                  label: Text(
                    _grupoSelecionado!.nomeGrupo,
                    style: const TextStyle(fontSize: 11),
                  ),
                  padding: EdgeInsets.zero,
                ),
            ],
          ),
        ),
        if (_grupoSelecionado == null)
          const Expanded(
            child: Center(
              child: Text(
                'Select a trip to start chatting',
                style: TextStyle(color: AppTheme.onSurfaceMuted),
              ),
            ),
          )
        else ...[
          Expanded(
            child: ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.all(12),
              itemCount: _msgs.length + (_iaLoading ? 1 : 0),
              itemBuilder: (_, i) {
                if (i == _msgs.length) {
                  return const Padding(
                    padding: EdgeInsets.all(8),
                    child: Row(
                      children: [
                        SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                        SizedBox(width: 8),
                        Text('Thinking...', style: TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 13)),
                      ],
                    ),
                  );
                }
                final m = _msgs[i];
                return Align(
                  alignment: m.isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    constraints: const BoxConstraints(maxWidth: 340),
                    decoration: BoxDecoration(
                      color: m.isUser ? AppTheme.primary : AppTheme.surfaceVariant,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: m.isUser
                        ? Text(m.text, style: const TextStyle(color: Colors.white, fontSize: 14))
                        : MarkdownBody(
                            data: m.text,
                            styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
                              p: const TextStyle(color: AppTheme.onSurface, fontSize: 14),
                            ),
                          ),
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
                  child: TextField(
                    controller: _chatCtrl,
                    decoration: const InputDecoration(
                      hintText: 'Ask anything about your trip...',
                    ),
                    onSubmitted: (_) => _enviarPergunta(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: _iaLoading ? null : _enviarPergunta,
                  icon: const Icon(Icons.send_rounded),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _Msg {
  final String text;
  final bool isUser;
  _Msg(this.text, this.isUser);
}
