import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/api_client.dart';
import '../../../core/constants.dart';
import '../../../core/web_style.dart';
import '../../../models/dashboard.dart';
import '../../../providers/language_provider.dart';
import '../../../services/grupo_service.dart';

/// Aba "pessoal" de viagem.html: minha visão financeira — quanto paguei,
/// minha dívida, últimos gastos, e o orçamento pessoal (editável). Recebe o
/// dashboard já carregado pelo [ViagemScreen] (compartilhado com Visão Geral
/// e Admin); ao salvar um novo orçamento, pede ao pai para recarregar tudo
/// — assim Visão Geral também reflete o novo total imediatamente.
class FinancesTab extends StatefulWidget {
  final int idGrupo;
  final DashboardCompleto? dash;
  final Future<void> Function() onReload;
  const FinancesTab({super.key, required this.idGrupo, required this.dash, required this.onReload});
  @override
  State<FinancesTab> createState() => _FinancesTabState();
}

class _FinancesTabState extends State<FinancesTab> {
  bool _editando = false;
  bool _salvando = false;
  String? _erro;
  final _orcamentoCtrl = TextEditingController();

  @override
  void dispose() {
    _orcamentoCtrl.dispose();
    super.dispose();
  }

  void _iniciarEdicao() {
    _orcamentoCtrl.text = widget.dash?.pessoal.meuOrcamento?.toStringAsFixed(2) ?? '';
    setState(() {
      _editando = true;
      _erro = null;
    });
  }

  Future<void> _salvar() async {
    final lang = context.read<LanguageProvider>();
    final valor = double.tryParse(_orcamentoCtrl.text.replaceAll(',', '.'));
    if (valor == null || valor < 0) {
      setState(() => _erro = lang.translate('finances.budgetError'));
      return;
    }
    setState(() {
      _salvando = true;
      _erro = null;
    });
    try {
      await GrupoService.alterarMeuOrcamento(widget.idGrupo, valor);
      setState(() => _editando = false);
      await widget.onReload();
    } catch (e) {
      setState(() => _erro = e is ApiException ? e.message : lang.translate('finances.budgetError'));
    } finally {
      if (mounted) setState(() => _salvando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    final dash = widget.dash;
    if (dash == null) {
      return const Center(child: CircularProgressIndicator(color: WebColors.primary));
    }
    final p = dash.pessoal;
    return RefreshIndicator(
      onRefresh: widget.onReload,
      color: WebColors.primary,
      backgroundColor: WebColors.bg,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 0, 14, 24),
        children: [
          TripCardExpanded(
            title: '👤 ${lang.translate('viagem.myView')}',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DashboardCard(
                  title: '🏦 ${lang.translate('finances.myFinances')}',
                  child: Column(
                    children: [
                      StatRow(label: lang.translate('finances.paid'), value: 'R\$ ${p.totalPagoPorMim.toStringAsFixed(2)}'),
                      StatRow(
                        label: lang.translate('finances.debt'),
                        value: 'R\$ ${p.minhaDividaAtual.toStringAsFixed(2)}',
                        valueColor: WebColors.danger,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                DashboardCard(
                  title: '📜 ${lang.translate('finances.recent')}',
                  child: p.ultimosGastos.isEmpty
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            child: Text(lang.translate('finances.noRecent'),
                                style: const TextStyle(color: WebColors.textMuted, fontSize: 14)),
                          ),
                        )
                      : Column(
                          children: p.ultimosGastos
                              .map((g) => CategoryItemRow(
                                    left: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          g.descricao.isEmpty
                                              ? (Constants.categoriaEmoji[g.categoria] ?? '') + g.categoria
                                              : g.descricao,
                                          style: const TextStyle(color: WebColors.text, fontSize: 14),
                                        ),
                                        Text(g.dataGasto,
                                            style: const TextStyle(color: WebColors.textMuted, fontSize: 11)),
                                      ],
                                    ),
                                    right: Text('R\$ ${g.valor.toStringAsFixed(2)}',
                                        style: const TextStyle(
                                            color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 14)),
                                  ))
                              .toList(),
                        ),
                ),
                const SizedBox(height: 16),
                DashboardCard(
                  title: '💰 ${lang.translate('finances.myBudget')}',
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      StatRow(
                        label: lang.translate('finances.budgetSet'),
                        value: p.meuOrcamento != null
                            ? 'R\$ ${p.meuOrcamento!.toStringAsFixed(2)}'
                            : lang.translate('finances.noBudget'),
                      ),
                      if (p.meuOrcamento != null)
                        StatRow(
                          label: lang.translate('finances.available'),
                          value: 'R\$ ${(p.disponivel ?? 0).toStringAsFixed(2)}',
                        ),
                      const SizedBox(height: 6),
                      if (_editando) ...[
                        TextField(
                          controller: _orcamentoCtrl,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          style: const TextStyle(color: WebColors.text, fontSize: 14),
                          decoration: InputDecoration(
                            filled: true,
                            fillColor: WebColors.surface2,
                            hintText: lang.translate('finances.budgetPlaceholder'),
                            hintStyle: const TextStyle(color: WebColors.textMuted),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(WebColors.radiusSm),
                              borderSide: const BorderSide(color: WebColors.border),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(WebColors.radiusSm),
                              borderSide: const BorderSide(color: WebColors.border),
                            ),
                          ),
                        ),
                        if (_erro != null) ...[
                          const SizedBox(height: 6),
                          Text(_erro!, style: const TextStyle(color: WebColors.danger, fontSize: 12)),
                        ],
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            GradientButton(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
                              onPressed: _salvando ? null : _salvar,
                              child: _salvando
                                  ? const SizedBox(
                                      height: 14, width: 14,
                                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                  : Text(lang.translate('finances.save'), style: const TextStyle(fontSize: 13)),
                            ),
                            const SizedBox(width: 8),
                            TextButton(
                              onPressed: () => setState(() => _editando = false),
                              style: TextButton.styleFrom(foregroundColor: WebColors.textMuted),
                              child: Text(lang.translate('finances.cancel')),
                            ),
                          ],
                        ),
                      ] else
                        Align(
                          alignment: Alignment.centerLeft,
                          child: OutlinedButton(
                            onPressed: _iniciarEdicao,
                            style: OutlinedButton.styleFrom(
                              foregroundColor: WebColors.text,
                              side: const BorderSide(color: WebColors.border),
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
                            ),
                            child: Text(lang.translate('finances.editBudget'), style: const TextStyle(fontSize: 13)),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
