import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/constants.dart';
import '../../../core/web_style.dart';
import '../../../models/dashboard.dart';
import '../../../providers/language_provider.dart';

/// Aba "geral" de viagem.html: dashboard do grupo — orçamento total, total
/// gasto, restante com barra de progresso, e distribuição por categoria.
/// Recebe o dashboard já carregado pelo [ViagemScreen] (compartilhado com
/// Minhas Finanças e Admin) em vez de buscar o seu próprio — assim, mudar o
/// orçamento pessoal em Minhas Finanças reflete aqui imediatamente.
class OverviewTab extends StatelessWidget {
  final DashboardCompleto? dash;
  final Future<void> Function() onReload;
  const OverviewTab({super.key, required this.dash, required this.onReload});

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    if (dash == null) {
      return const Center(child: CircularProgressIndicator(color: WebColors.primary));
    }
    final g = dash!.geral;
    final temOrcamento = g.orcamentoTotal > 0;
    return RefreshIndicator(
      onRefresh: onReload,
      color: WebColors.primary,
      backgroundColor: WebColors.bg,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 0, 14, 24),
        children: [
          TripCardExpanded(
            title: '📊 ${lang.translate('viagem.dashboard')}',
            child: Wrap(
              spacing: 16,
              runSpacing: 16,
              children: [
                SizedBox(
                  width: _cardWidth(context),
                  child: DashboardCard(
                    title: '💰 ${lang.translate('viagem.budget')}',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        StatRow(
                          label: lang.translate('viagem.budgetTotal'),
                          value: 'R\$ ${g.orcamentoTotal.toStringAsFixed(2)}',
                        ),
                        StatRow(
                          label: lang.translate('overview.totalSpent'),
                          value: 'R\$ ${g.totalConsumido.toStringAsFixed(2)}',
                        ),
                        if (temOrcamento)
                          StatRow(
                            label: lang.translate('overview.remainingBudget'),
                            value: 'R\$ ${g.orcamentoRestante.toStringAsFixed(2)}',
                          ),
                        const SizedBox(height: 4),
                        WebProgressBar(value: temOrcamento ? g.percentualConsumido / 100 : 0),
                        const SizedBox(height: 8),
                        Center(
                          child: Text(
                            temOrcamento
                                ? '${g.percentualConsumido}% ${lang.translate('overview.used')}'
                                : '— ${lang.translate('overview.used')}',
                            style: const TextStyle(fontSize: 12, color: WebColors.textMuted),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(
                  width: _cardWidth(context),
                  child: DashboardCard(
                    title: '🏷️ ${lang.translate('viagem.categories')}',
                    child: g.distribuicao.isEmpty
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(vertical: 8),
                              child: Text(lang.translate('viagem.noExpenses'),
                                  style: const TextStyle(color: WebColors.textMuted, fontSize: 14)),
                            ),
                          )
                        : Column(
                            children: g.distribuicao
                                .map((c) => CategoryItemRow(
                                      left: Text(
                                        '${Constants.categoriaEmoji[c.categoria] ?? '📦'}  ${c.categoria}',
                                        style: const TextStyle(color: WebColors.text, fontSize: 14),
                                      ),
                                      right: Text('R\$ ${c.total.toStringAsFixed(2)}',
                                          style: const TextStyle(
                                              color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 14)),
                                    ))
                                .toList(),
                          ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  double _cardWidth(BuildContext context) {
    final w = MediaQuery.of(context).size.width - 28 - 40 - 16; // padding + card padding + gap
    return w < 260 ? w : (w > 560 ? (w - 16) / 2 : w);
  }
}
