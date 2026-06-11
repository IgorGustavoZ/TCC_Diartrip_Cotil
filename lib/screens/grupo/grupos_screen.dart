import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../core/theme.dart';
import '../../models/grupo.dart';
import '../../services/grupo_service.dart';
import '../../services/ia_service.dart';
import '../../widgets/app_drawer.dart';
import '../../widgets/trip_card.dart';

class GruposScreen extends StatefulWidget {
  const GruposScreen({super.key});
  @override
  State<GruposScreen> createState() => _GruposScreenState();
}

class _GruposScreenState extends State<GruposScreen> {
  List<Grupo> _grupos = [];
  List<Grupo>? _resultadoBusca;
  bool _loading = true;
  final _codigoCtrl = TextEditingController();
  final _buscaCtrl = TextEditingController();
  bool _entrando = false;
  bool _buscando = false;
  String? _msg;
  bool _msgErro = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _codigoCtrl.dispose();
    _buscaCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      _grupos = await GrupoService.listar();
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _buscar(String q) async {
    if (q.trim().isEmpty) {
      setState(() => _resultadoBusca = null);
      return;
    }
    setState(() => _buscando = true);
    try {
      final r = await GrupoService.buscar(q.trim());
      if (mounted) setState(() => _resultadoBusca = r);
    } catch (_) {
      if (mounted) setState(() => _resultadoBusca = []);
    } finally {
      if (mounted) setState(() => _buscando = false);
    }
  }

  Future<void> _entrar() async {
    final codigo = _codigoCtrl.text.trim();
    if (codigo.length < 4) {
      setState(() { _msg = 'Código inválido'; _msgErro = true; });
      return;
    }
    setState(() { _entrando = true; _msg = null; });
    try {
      await GrupoService.entrar(codigo);
      _codigoCtrl.clear();
      setState(() { _msg = 'Entrou no grupo com sucesso!'; _msgErro = false; });
      await _load();
    } catch (e) {
      setState(() { _msg = e.toString(); _msgErro = true; });
    } finally {
      if (mounted) setState(() => _entrando = false);
    }
  }

  // ── Tap → abre chat IA ──────────────────────────────────────────────────────
  void _abrirChatIa(Grupo g) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppTheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _IaChatSheet(
        grupo: g,
        onAbrirViagem: () => Navigator.pushNamed(context, '/viagem/${g.id}'),
      ),
    );
  }

  // ── Long press → abre informações ──────────────────────────────────────────
  void _abrirInfo(Grupo g) {
    HapticFeedback.mediumImpact();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppTheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _TripInfoSheet(
        grupo: g,
        onAbrirViagem: () => Navigator.pushNamed(context, '/viagem/${g.id}'),
        onAbrirIa: () => _abrirChatIa(g),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Groups')),
      drawer: const AppDrawer(activeRoute: '/grupos'),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.pushNamed(context, '/nova-viagem'),
        icon: const Icon(Icons.add),
        label: const Text('New Trip'),
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Entrar via código
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Join a group', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                    const SizedBox(height: 4),
                    const Text('Enter the invite code to join an existing trip.',
                        style: TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 13)),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _codigoCtrl,
                            decoration: const InputDecoration(
                              hintText: 'Invite code',
                              prefixIcon: Icon(Icons.vpn_key_outlined, size: 18),
                            ),
                            textCapitalization: TextCapitalization.characters,
                          ),
                        ),
                        const SizedBox(width: 10),
                        ElevatedButton(
                          onPressed: _entrando ? null : _entrar,
                          child: _entrando
                              ? const SizedBox(
                                  height: 16,
                                  width: 16,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                )
                              : const Text('Join'),
                        ),
                      ],
                    ),
                    if (_msg != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        _msg!,
                        style: TextStyle(
                          color: _msgErro ? AppTheme.error : AppTheme.success,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // ── Busca de grupos ─────────────────────────────────────
            TextField(
              controller: _buscaCtrl,
              decoration: InputDecoration(
                hintText: 'Search groups...',
                prefixIcon: const Icon(Icons.search, size: 18),
                suffixIcon: _buscando
                    ? const Padding(
                        padding: EdgeInsets.all(10),
                        child: SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      )
                    : _buscaCtrl.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.close, size: 18),
                            onPressed: () {
                              _buscaCtrl.clear();
                              setState(() => _resultadoBusca = null);
                            },
                          )
                        : null,
              ),
              onChanged: (v) => _buscar(v),
            ),
            const SizedBox(height: 16),
            Text(
              _resultadoBusca != null ? 'Search Results' : 'My Trips',
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
            ),
            // Dica de gestos
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.auto_awesome, size: 12, color: AppTheme.primary.withValues(alpha: 0.7)),
                const SizedBox(width: 4),
                const Text('Tap to chat with AI  ·  Hold for trip details',
                    style: TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 11)),
              ],
            ),
            const SizedBox(height: 10),
            if (_loading && _resultadoBusca == null)
              const Center(child: CircularProgressIndicator())
            else if ((_resultadoBusca ?? _grupos).isEmpty)
              Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                    _resultadoBusca != null ? 'No groups found.' : 'No trips yet.',
                    style: const TextStyle(color: AppTheme.onSurfaceMuted),
                  ),
                ),
              )
            else
              ...List.generate(
                (_resultadoBusca ?? _grupos).length,
                (i) {
                  final g = (_resultadoBusca ?? _grupos)[i];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: TripCard(
                      grupo: g,
                      onTap: () => _abrirChatIa(g),
                      onLongPress: () => _abrirInfo(g),
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// Chat IA — bottom sheet
// ──────────────────────────────────────────────────────────────────────────────

typedef _Msg = ({String texto, bool isUser, bool isError});

class _IaChatSheet extends StatefulWidget {
  final Grupo grupo;
  final VoidCallback onAbrirViagem;

  const _IaChatSheet({required this.grupo, required this.onAbrirViagem});

  @override
  State<_IaChatSheet> createState() => _IaChatSheetState();
}

class _IaChatSheetState extends State<_IaChatSheet> {
  final _ctrl = TextEditingController();
  final _scroll = ScrollController();
  final List<_Msg> _msgs = [];
  bool _loading = false;

  static const _sugestoes = [
    'O que levar nessa viagem?',
    'Dicas de orçamento',
    'Pontos turísticos imperdíveis',
    'Melhor época para ir',
  ];

  @override
  void dispose() {
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _enviar([String? texto]) async {
    final pergunta = (texto ?? _ctrl.text).trim();
    if (pergunta.isEmpty || _loading) return;
    _ctrl.clear();
    setState(() {
      _msgs.add((texto: pergunta, isUser: true, isError: false));
      _loading = true;
    });
    _scrollBottom();
    try {
      final resp = await IaService.perguntar(
        pergunta: pergunta,
        idGrupo: widget.grupo.id,
      );
      if (mounted) {
        setState(() => _msgs.add((texto: resp, isUser: false, isError: false)));
        _scrollBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _msgs.add((
          texto: 'Não foi possível obter resposta. Tente novamente.',
          isUser: false,
          isError: true,
        )));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _scrollBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    final height = MediaQuery.of(context).size.height * 0.88;

    return SizedBox(
      height: height,
      child: Column(
        children: [
          // Handle bar
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 6),
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: AppTheme.onSurfaceMuted.withValues(alpha: 0.35),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          // Header
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 8, 10),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(9),
                  decoration: BoxDecoration(
                    color: AppTheme.primary.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.auto_awesome, color: AppTheme.primary, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Assistente de Viagem IA',
                          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                      Text(widget.grupo.nomeGrupo,
                          style: const TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 12)),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.open_in_new, size: 20, color: AppTheme.onSurfaceMuted),
                  tooltip: 'Abrir viagem completa',
                  onPressed: () {
                    Navigator.pop(context);
                    widget.onAbrirViagem();
                  },
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),
          Divider(height: 1, color: Colors.white.withValues(alpha: 0.07)),
          // Área de mensagens
          Expanded(
            child: _msgs.isEmpty ? _emptyState() : _messageList(),
          ),
          // Loading indicator
          if (_loading)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: AppTheme.surfaceVariant,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _Dot(delay: 0),
                        SizedBox(width: 4),
                        _Dot(delay: 150),
                        SizedBox(width: 4),
                        _Dot(delay: 300),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          // Campo de input
          Padding(
            padding: EdgeInsets.fromLTRB(12, 8, 12, bottom + 12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _ctrl,
                    decoration: const InputDecoration(
                      hintText: 'Pergunte sobre a viagem...',
                      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    ),
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _enviar(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: _loading ? null : () => _enviar(),
                  icon: const Icon(Icons.send_rounded, size: 20),
                  style: IconButton.styleFrom(
                    backgroundColor: AppTheme.primary,
                    disabledBackgroundColor: AppTheme.surfaceVariant,
                    padding: const EdgeInsets.all(12),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _emptyState() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.primary.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.travel_explore, size: 40, color: AppTheme.primary),
          ),
          const SizedBox(height: 16),
          Text(
            widget.grupo.destinoPrincipal,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
          ),
          const SizedBox(height: 6),
          const Text(
            'Pergunte qualquer coisa sobre\nsua viagem e o destino',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 13),
          ),
          const SizedBox(height: 24),
          // Chips de sugestão
          Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: _sugestoes
                .map((s) => ActionChip(
                      label: Text(s, style: const TextStyle(fontSize: 12)),
                      onPressed: () => _enviar(s),
                      backgroundColor: AppTheme.surfaceVariant,
                      side: BorderSide(color: AppTheme.primary.withValues(alpha: 0.3)),
                    ))
                .toList(),
          ),
        ],
      ),
    );
  }

  Widget _messageList() {
    return ListView.builder(
      controller: _scroll,
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
      itemCount: _msgs.length,
      itemBuilder: (_, i) {
        final m = _msgs[i];
        if (m.isUser) {
          return Align(
            alignment: Alignment.centerRight,
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 4),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.78,
              ),
              decoration: BoxDecoration(
                color: AppTheme.primary,
                borderRadius: BorderRadius.circular(16).copyWith(
                  bottomRight: const Radius.circular(4),
                ),
              ),
              child: Text(m.texto,
                  style: const TextStyle(color: Colors.white, fontSize: 14)),
            ),
          );
        }
        return Align(
          alignment: Alignment.centerLeft,
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 4),
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.88,
            ),
            decoration: BoxDecoration(
              color: m.isError
                  ? AppTheme.error.withValues(alpha: 0.15)
                  : AppTheme.surfaceVariant,
              borderRadius: BorderRadius.circular(16).copyWith(
                bottomLeft: const Radius.circular(4),
              ),
            ),
            child: m.isError
                ? Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline, size: 16, color: AppTheme.error),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(m.texto,
                            style: const TextStyle(color: AppTheme.error, fontSize: 13)),
                      ),
                    ],
                  )
                : MarkdownBody(
                    data: m.texto,
                    styleSheet: MarkdownStyleSheet(
                      p: const TextStyle(color: AppTheme.onSurface, fontSize: 14, height: 1.4),
                      strong: const TextStyle(
                          color: AppTheme.onSurface, fontWeight: FontWeight.w700, fontSize: 14),
                      em: const TextStyle(color: AppTheme.onSurface, fontStyle: FontStyle.italic, fontSize: 14),
                      listBullet: const TextStyle(color: AppTheme.onSurface, fontSize: 14),
                      code: const TextStyle(
                          color: AppTheme.accent, fontSize: 13, fontFamily: 'monospace'),
                      blockquoteDecoration: BoxDecoration(
                        border: Border(
                          left: BorderSide(
                              color: AppTheme.primary.withValues(alpha: 0.6), width: 3),
                        ),
                      ),
                    ),
                  ),
          ),
        );
      },
    );
  }
}

// Indicador de "digitando" (3 pontos animados)
class _Dot extends StatefulWidget {
  final int delay;
  const _Dot({required this.delay});
  @override
  State<_Dot> createState() => _DotState();
}

class _DotState extends State<_Dot> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _anim = Tween<double>(begin: 0.3, end: 1).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
    Future.delayed(Duration(milliseconds: widget.delay), () {
      if (mounted) _ctrl.repeat(reverse: true);
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _anim,
      child: Container(
        width: 7,
        height: 7,
        decoration: const BoxDecoration(
          color: AppTheme.onSurfaceMuted,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// Informações da viagem — bottom sheet
// ──────────────────────────────────────────────────────────────────────────────

class _TripInfoSheet extends StatelessWidget {
  final Grupo grupo;
  final VoidCallback onAbrirViagem;
  final VoidCallback onAbrirIa;

  const _TripInfoSheet({
    required this.grupo,
    required this.onAbrirViagem,
    required this.onAbrirIa,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(
          20, 0, 20, MediaQuery.of(context).viewInsets.bottom + 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle bar
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 16),
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: AppTheme.onSurfaceMuted.withValues(alpha: 0.35),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          // Cabeçalho
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.flight_takeoff, color: AppTheme.primary, size: 26),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(grupo.nomeGrupo,
                        style: const TextStyle(
                            fontWeight: FontWeight.w700, fontSize: 17)),
                    Text(grupo.destinoPrincipal,
                        style: const TextStyle(
                            color: AppTheme.onSurfaceMuted, fontSize: 13)),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Divider(height: 1, color: Colors.white.withValues(alpha: 0.07)),
          const SizedBox(height: 16),
          // Informações
          if (grupo.dataInicio != null)
            _infoRow(
              Icons.calendar_today_outlined,
              'Período',
              '${grupo.dataInicio} → ${grupo.dataFim ?? 'a definir'}',
            ),
          if (grupo.orcamento != null)
            _infoRow(
              Icons.attach_money,
              'Orçamento',
              'R\$ ${grupo.orcamento!.toStringAsFixed(2)}',
            ),
          if (grupo.tipoViagem != null)
            _infoRow(Icons.category_outlined, 'Tipo', grupo.tipoViagem!),
          if (grupo.preferencias != null && grupo.preferencias!.isNotEmpty)
            _infoRow(Icons.favorite_outline, 'Preferências', grupo.preferencias!),
          // Código de convite com cópia
          if (grupo.codigoConvite != null) ...[
            const SizedBox(height: 8),
            const Text('Código de convite',
                style: TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 12)),
            const SizedBox(height: 6),
            GestureDetector(
              onTap: () {
                Clipboard.setData(ClipboardData(text: grupo.codigoConvite!));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Código copiado!')),
                );
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceVariant,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                      color: AppTheme.primary.withValues(alpha: 0.3)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      grupo.codigoConvite!,
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 4,
                      ),
                    ),
                    const Icon(Icons.copy, color: AppTheme.primary, size: 18),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 24),
          // Botões de ação
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.auto_awesome, size: 16),
                  label: const Text('Chat IA'),
                  onPressed: () {
                    Navigator.pop(context);
                    onAbrirIa();
                  },
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.open_in_new, size: 16),
                  label: const Text('Abrir viagem'),
                  onPressed: () {
                    Navigator.pop(context);
                    onAbrirViagem();
                  },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 18, color: AppTheme.onSurfaceMuted),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        color: AppTheme.onSurfaceMuted, fontSize: 11)),
                Text(value,
                    style: const TextStyle(fontSize: 14)),
              ],
            ),
          ],
        ),
      );
}
