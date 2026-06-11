import 'package:flutter/material.dart';
import '../../../core/app_logger.dart';
import '../../../core/constants.dart';
import '../../../core/theme.dart';
import '../../../models/dashboard.dart';
import '../../../services/dashboard_service.dart';

class OverviewTab extends StatefulWidget {
  final int idGrupo;
  const OverviewTab({super.key, required this.idGrupo});
  @override
  State<OverviewTab> createState() => _OverviewTabState();
}

class _OverviewTabState extends State<OverviewTab> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;
  DashboardCompleto? _dash;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final d = await DashboardService.get(widget.idGrupo);
      if (mounted) setState(() => _dash = d);
    } catch (e, s) {
      AppLogger.captureError('OverviewTab._load', e, s);
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    if (_dash == null) return const Center(child: CircularProgressIndicator());
    final g = _dash!.geral;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _statRow('Total Spent', 'R\$ ${g.totalConsumido.toStringAsFixed(2)}'),
          _statRow('Remaining Budget', 'R\$ ${g.orcamentoRestante.toStringAsFixed(2)}'),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: g.percentualConsumido / 100,
              backgroundColor: AppTheme.surfaceVariant,
              color: g.percentualConsumido > 80 ? AppTheme.error : AppTheme.primary,
              minHeight: 10,
            ),
          ),
          Align(
            alignment: Alignment.centerRight,
            child: Text('${g.percentualConsumido}% used',
                style: const TextStyle(fontSize: 12, color: AppTheme.onSurfaceMuted)),
          ),
          const SizedBox(height: 16),
          const Text('By Category', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          ...g.distribuicao.map((c) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Text(Constants.categoriaEmoji[c.categoria] ?? '📦',
                        style: const TextStyle(fontSize: 18)),
                    const SizedBox(width: 10),
                    Expanded(child: Text(c.categoria)),
                    Text('R\$ ${c.total.toStringAsFixed(2)}',
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                  ],
                ),
              )),
        ],
      ),
    );
  }

  Widget _statRow(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(color: AppTheme.onSurfaceMuted)),
            Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
          ],
        ),
      );
}
