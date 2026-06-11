import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/app_logger.dart';
import '../../core/theme.dart';
import '../../models/grupo.dart';
import '../../providers/auth_provider.dart';
import '../../services/grupo_service.dart';
import '../../widgets/app_drawer.dart';
import 'tabs/admin_tab.dart';
import 'tabs/chat_tab.dart';
import 'tabs/expenses_tab.dart';
import 'tabs/finances_tab.dart';
import 'tabs/info_tab.dart';
import 'tabs/itinerary_tab.dart';
import 'tabs/overview_tab.dart';
import 'tabs/photos_tab.dart';

class ViagemScreen extends StatefulWidget {
  final int idGrupo;
  const ViagemScreen({super.key, required this.idGrupo});
  @override
  State<ViagemScreen> createState() => _ViagemScreenState();
}

class _ViagemScreenState extends State<ViagemScreen>
    with TickerProviderStateMixin {
  late TabController _tabCtrl;
  Grupo? _grupo;
  List<Membro> _membros = [];
  bool _loading = true;
  int _meId = 0;
  bool _isMeAdmin = false;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 8, vsync: this);
    _load();
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    _meId = context.read<AuthProvider>().usuario?.id ?? 0;
    try {
      final results = await Future.wait([
        GrupoService.get(widget.idGrupo),
        GrupoService.listarMembros(widget.idGrupo),
      ]);
      _grupo = results[0] as Grupo;
      _membros = results[1] as List<Membro>;
      _isMeAdmin = _membros.any((m) => m.id == _meId && m.isAdmin);
    } catch (e, s) {
      AppLogger.captureError('ViagemScreen._load', e, s);
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (_grupo == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Trip')),
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.wifi_off_outlined,
                  size: 48, color: AppTheme.onSurfaceMuted),
              const SizedBox(height: 12),
              const Text('Failed to load trip data.',
                  style: TextStyle(color: AppTheme.onSurfaceMuted)),
              const SizedBox(height: 16),
              OutlinedButton(
                  onPressed: _load, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_grupo!.nomeGrupo,
                style: const TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w700)),
            Text(_grupo!.destinoPrincipal,
                style: const TextStyle(
                    fontSize: 12, color: AppTheme.onSurfaceMuted)),
          ],
        ),
        bottom: TabBar(
          controller: _tabCtrl,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'My Finances'),
            Tab(text: 'Admin'),
            Tab(text: 'Expenses'),
            Tab(text: 'Itinerary'),
            Tab(text: 'Photos'),
            Tab(text: 'Chat'),
            Tab(text: 'Info'),
          ],
        ),
      ),
      drawer: AppDrawer(activeRoute: '/viagem/${widget.idGrupo}'),
      body: TabBarView(
        controller: _tabCtrl,
        children: [
          OverviewTab(idGrupo: widget.idGrupo),
          FinancesTab(idGrupo: widget.idGrupo),
          AdminTab(
            idGrupo: widget.idGrupo,
            membros: _membros,
            meId: _meId,
            isAdmin: _isMeAdmin,
            onReload: _load,
          ),
          ExpensesTab(
            idGrupo: widget.idGrupo,
            meId: _meId,
            membros: _membros,
          ),
          ItineraryTab(idGrupo: widget.idGrupo, isAdmin: _isMeAdmin),
          PhotosTab(idGrupo: widget.idGrupo, meId: _meId),
          ChatTab(
            idGrupo: widget.idGrupo,
            meId: _meId,
            membros: _membros,
          ),
          InfoTab(grupo: _grupo!),
        ],
      ),
    );
  }
}
