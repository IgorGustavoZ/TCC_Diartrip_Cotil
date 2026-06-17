import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/app_logger.dart';
import '../../../core/theme.dart';
import '../../../models/dashboard.dart';
import '../../../models/grupo.dart';
import '../../../providers/language_provider.dart';
import '../../../services/dashboard_service.dart';
import '../../../services/grupo_service.dart';
import '../../../widgets/avatar_widget.dart';

class AdminTab extends StatefulWidget {
  final int idGrupo;
  final List<Membro> membros;
  final int meId;
  final bool isAdmin;
  final VoidCallback onReload;

  const AdminTab({
    super.key,
    required this.idGrupo,
    required this.membros,
    required this.meId,
    required this.isAdmin,
    required this.onReload,
  });

  @override
  State<AdminTab> createState() => _AdminTabState();
}

class _AdminTabState extends State<AdminTab> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;
  DashboardAdmin? _adminData;

  @override
  void initState() {
    super.initState();
    if (widget.isAdmin) _loadAdmin();
  }

  Future<void> _loadAdmin() async {
    try {
      final d = await DashboardService.get(widget.idGrupo);
      if (mounted) setState(() => _adminData = d.admin);
    } catch (e, s) {
      AppLogger.captureError('AdminTab._loadAdmin', e, s);
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final lang = context.watch<LanguageProvider>();

    if (!widget.isAdmin) {
      return Center(
        child: Text(lang.translate('admin.required'),
            style: const TextStyle(color: AppTheme.onSurfaceMuted)),
      );
    }
    return RefreshIndicator(
      onRefresh: () async {
        await _loadAdmin();
        widget.onReload();
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_adminData != null) ...[
            Text(lang.translate('admin.statistics'),
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 10),
            Row(
              children: [
                _statCard(lang.translate('admin.activeMembers'),
                    '${_adminData!.estatisticas.membrosAtivos}',
                    Icons.people_outline),
                const SizedBox(width: 10),
                _statCard(lang.translate('admin.photos'),
                    '${_adminData!.estatisticas.totalFotosSubidas}',
                    Icons.photo_outlined),
                const SizedBox(width: 10),
                _statCard(lang.translate('admin.itinerary'),
                    '${_adminData!.estatisticas.itensNoRoteiro}',
                    Icons.map_outlined),
              ],
            ),
            const SizedBox(height: 20),
            Text(lang.translate('admin.ranking'),
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 10),
            ...List.generate(_adminData!.ranking.length, (i) {
              final r = _adminData!.ranking[i];
              final medals = ['🥇', '🥈', '🥉'];
              final medal = i < medals.length ? medals[i] : '${i + 1}.';
              return Card(
                child: ListTile(
                  leading: Text(medal, style: const TextStyle(fontSize: 22)),
                  title: Text(r.nome, style: const TextStyle(fontSize: 14)),
                  trailing: Text(
                    'R\$ ${r.total.toStringAsFixed(2)}',
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, color: AppTheme.primary),
                  ),
                ),
              );
            }),
            const SizedBox(height: 20),
          ] else
            const Center(
                child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(),
            )),
          Text(lang.translate('admin.members'),
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          const SizedBox(height: 10),
          ...widget.membros.map((m) => Card(
                child: ListTile(
                  leading: AvatarWidget(
                    fotoUrl: m.fotoPerfil,
                    iniciais: m.nome.isNotEmpty ? m.nome[0].toUpperCase() : '?',
                    radius: 18,
                  ),
                  title: Text(m.nome, style: const TextStyle(fontSize: 14)),
                  subtitle: Text(m.cargo, style: const TextStyle(fontSize: 12)),
                  trailing: m.id != widget.meId
                      ? PopupMenuButton<String>(
                          itemBuilder: (_) => [
                            if (!m.isAdmin)
                              PopupMenuItem(
                                  value: 'promover',
                                  child: Text(lang.translate('admin.promote'))),
                            if (m.isAdmin)
                              PopupMenuItem(
                                  value: 'rebaixar',
                                  child: Text(lang.translate('admin.demote'))),
                          ],
                          onSelected: (v) async {
                            try {
                              if (v == 'promover') {
                                await GrupoService.promover(widget.idGrupo, m.id);
                              }
                              if (v == 'rebaixar') {
                                await GrupoService.rebaixar(widget.idGrupo, m.id);
                              }
                              widget.onReload();
                            } catch (e) {
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(content: Text(e.toString())));
                              }
                            }
                          },
                        )
                      : Chip(
                          label:
                              Text(lang.translate('admin.you'), style: const TextStyle(fontSize: 11))),
                ),
              )),
        ],
      ),
    );
  }

  Widget _statCard(String label, String value, IconData icon) => Expanded(
        child: Card(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
            child: Column(
              children: [
                Icon(icon, color: AppTheme.primary, size: 22),
                const SizedBox(height: 6),
                Text(value,
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, fontSize: 18)),
                Text(label,
                    style: const TextStyle(
                        color: AppTheme.onSurfaceMuted, fontSize: 11),
                    textAlign: TextAlign.center),
              ],
            ),
          ),
        ),
      );
}
