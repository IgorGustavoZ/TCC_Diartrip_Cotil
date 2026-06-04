import 'package:flutter/material.dart';
import '../../../core/app_logger.dart';
import '../../../core/constants.dart';
import '../../../core/theme.dart';
import '../../../models/dashboard.dart';
import '../../../services/dashboard_service.dart';

class FinancesTab extends StatefulWidget {
  final int idGrupo;
  const FinancesTab({super.key, required this.idGrupo});
  @override
  State<FinancesTab> createState() => _FinancesTabState();
}

class _FinancesTabState extends State<FinancesTab> with AutomaticKeepAliveClientMixin {
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
      AppLogger.captureError('FinancesTab._load', e, s);
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    if (_dash == null) return const Center(child: CircularProgressIndicator());
    final p = _dash!.pessoal;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _card('I paid', 'R\$ ${p.totalPagoPorMim.toStringAsFixed(2)}',
              Icons.payment, AppTheme.success),
          const SizedBox(height: 10),
          _card('My debt', 'R\$ ${p.minhaDividaAtual.toStringAsFixed(2)}',
              Icons.account_balance_wallet, AppTheme.warning),
          const SizedBox(height: 16),
          const Text('Recent Expenses', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          ...p.ultimosGastos.map((g) => Card(
                child: ListTile(
                  leading: Text(Constants.categoriaEmoji[g.categoria] ?? '📦',
                      style: const TextStyle(fontSize: 22)),
                  title: Text(g.descricao.isEmpty ? g.categoria : g.descricao,
                      style: const TextStyle(fontSize: 14)),
                  subtitle: Text(g.dataGasto, style: const TextStyle(fontSize: 12)),
                  trailing: Text('R\$ ${g.valor.toStringAsFixed(2)}',
                      style: const TextStyle(
                          fontWeight: FontWeight.w600, color: AppTheme.primary)),
                ),
              )),
        ],
      ),
    );
  }

  Widget _card(String label, String value, IconData icon, Color color) => Card(
        child: ListTile(
          leading: CircleAvatar(
            backgroundColor: color.withValues(alpha: 0.15),
            child: Icon(icon, color: color, size: 20),
          ),
          title: Text(label,
              style: const TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 13)),
          trailing: Text(value,
              style: TextStyle(
                  color: color, fontWeight: FontWeight.w700, fontSize: 16)),
        ),
      );
}
