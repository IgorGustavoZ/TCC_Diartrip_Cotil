import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../../core/api_client.dart';
import '../../../core/app_logger.dart';
import '../../../core/constants.dart';
import '../../../core/web_style.dart';
import '../../../models/gasto.dart';
import '../../../models/grupo.dart';
import '../../../providers/language_provider.dart';
import '../../../services/gasto_service.dart';
import '../../../widgets/confirm_dialog.dart';

/// Aba "gastos" de viagem.html: registrar gasto (`.form-gasto`) + histórico
/// do grupo (`.gasto-item`).
class ExpensesTab extends StatefulWidget {
  final int idGrupo;
  final int meId;
  final List<Membro> membros;
  /// Datas da viagem (`grupo.data_inicio`/`data_fim`) — o seletor de data do
  /// gasto só permite escolher dias dentro desse intervalo. Vem sempre
  /// atualizado do [ViagemScreen], então editar as datas da viagem (aba
  /// Info) já reflete aqui automaticamente.
  final String? dataInicioViagem;
  final String? dataFimViagem;
  /// Recarrega o dashboard compartilhado no [ViagemScreen] — sem isso,
  /// Visão Geral/Minhas Finanças/Admin ficam com valores desatualizados até
  /// a próxima vez que a viagem for reaberta.
  final Future<void> Function() onReload;

  const ExpensesTab({
    super.key,
    required this.idGrupo,
    required this.meId,
    required this.membros,
    required this.dataInicioViagem,
    required this.dataFimViagem,
    required this.onReload,
  });

  @override
  State<ExpensesTab> createState() => _ExpensesTabState();
}

class _ExpensesTabState extends State<ExpensesTab>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  List<Gasto> _gastos = [];
  bool _loading = true;
  final _valorCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  String _categoria = 'Alimentação';
  DateTime? _dataGasto;
  Set<int> _selectedMembros = {};
  bool _saving = false;
  String? _erro;

  static final _dateFmt = DateFormat('yyyy-MM-dd');

  DateTime? get _tripStart => widget.dataInicioViagem != null ? DateTime.tryParse(widget.dataInicioViagem!) : null;
  DateTime? get _tripEnd => widget.dataFimViagem != null ? DateTime.tryParse(widget.dataFimViagem!) : null;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant ExpensesTab old) {
    super.didUpdateWidget(old);
    // Se a viagem mudou de data (aba Info) e a data já escolhida no
    // formulário ficou fora do novo intervalo, limpa pra evitar enviar um
    // gasto com uma data que não é mais válida.
    final gasto = _dataGasto;
    if (gasto == null) return;
    final inicio = _tripStart;
    final fim = _tripEnd;
    if ((inicio != null && gasto.isBefore(inicio)) || (fim != null && gasto.isAfter(fim))) {
      setState(() => _dataGasto = null);
    }
  }

  @override
  void dispose() {
    _valorCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final g = await GastoService.listar(widget.idGrupo);
      if (mounted) setState(() { _gastos = g; _loading = false; });
    } catch (e, s) {
      AppLogger.captureError('ExpensesTab._load', e, s);
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final firstDate = _tripStart ?? DateTime(now.year - 2);
    var lastDate = _tripEnd ?? now;
    if (lastDate.isBefore(firstDate)) lastDate = firstDate;
    var initialDate = _dataGasto ?? now;
    if (initialDate.isBefore(firstDate)) initialDate = firstDate;
    if (initialDate.isAfter(lastDate)) initialDate = lastDate;
    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: firstDate,
      lastDate: lastDate,
    );
    if (picked != null) setState(() => _dataGasto = picked);
  }

  Future<void> _addGasto() async {
    final lang = context.read<LanguageProvider>();
    final valor = double.tryParse(_valorCtrl.text.replaceAll(',', '.'));
    if (valor == null || valor <= 0) {
      setState(() => _erro = lang.translate('viagem.expenseError'));
      return;
    }
    setState(() { _saving = true; _erro = null; });
    try {
      await GastoService.criar(
        idGrupo: widget.idGrupo,
        valor: valor,
        categoria: _categoria,
        descricao: _descCtrl.text.trim(),
        dataGasto: _dataGasto != null ? _dateFmt.format(_dataGasto!) : null,
        idUsuariosDivisao:
            _selectedMembros.isEmpty ? null : _selectedMembros.toList(),
      );
      _valorCtrl.clear();
      _descCtrl.clear();
      setState(() { _dataGasto = null; _selectedMembros = {}; });
      await _load();
      await widget.onReload();
    } catch (e) {
      setState(() => _erro = e is ApiException ? e.message : lang.translate('viagem.expenseError'));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _editGasto(Gasto gasto) async {
    final lang = context.read<LanguageProvider>();
    final valorCtrl =
        TextEditingController(text: gasto.valor.toStringAsFixed(2));
    final descCtrl = TextEditingController(text: gasto.descricao ?? '');
    var cat = gasto.categoria;
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (ctx, setDialog) => AlertDialog(
          backgroundColor: WebColors.bg2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(WebColors.radiusLg)),
          title: Text(lang.translate('expenses.edit'), style: const TextStyle(color: WebColors.text)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _dialogField(valorCtrl, lang.translate('expenses.value'),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true)),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                initialValue: cat,
                dropdownColor: WebColors.bg2,
                style: const TextStyle(color: WebColors.text, fontSize: 14),
                decoration: _dialogDecoration(lang.translate('expenses.category')),
                items: Constants.categorias
                    .map((c) => DropdownMenuItem(
                          value: c,
                          child: Text('${Constants.categoriaEmoji[c] ?? ''} $c'),
                        ))
                    .toList(),
                onChanged: (v) => setDialog(() => cat = v ?? cat),
              ),
              const SizedBox(height: 10),
              _dialogField(descCtrl, lang.translate('expenses.description')),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                style: TextButton.styleFrom(foregroundColor: WebColors.textMuted),
                child: Text(lang.translate('expenses.cancel'))),
            TextButton(
                onPressed: () => Navigator.pop(ctx, true),
                style: TextButton.styleFrom(foregroundColor: WebColors.primary),
                child: Text(lang.translate('expenses.save'), style: const TextStyle(fontWeight: FontWeight.w700))),
          ],
        ),
      ),
    );
    if (ok != true) return;
    final novoValor =
        double.tryParse(valorCtrl.text.replaceAll(',', '.'));
    if (novoValor == null || novoValor <= 0) return;
    try {
      await GastoService.atualizar(
        idGasto: gasto.id,
        valor: novoValor,
        categoria: cat,
        descricao: descCtrl.text.trim(),
      );
      await _load();
      await widget.onReload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  InputDecoration _dialogDecoration(String label) => InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: WebColors.textMuted, fontSize: 13),
        filled: true,
        fillColor: WebColors.surface2,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(WebColors.radiusSm), borderSide: const BorderSide(color: WebColors.border)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(WebColors.radiusSm), borderSide: const BorderSide(color: WebColors.border)),
      );

  Widget _dialogField(TextEditingController ctrl, String label, {TextInputType? keyboardType}) => TextField(
        controller: ctrl,
        keyboardType: keyboardType,
        style: const TextStyle(color: WebColors.text, fontSize: 14),
        decoration: _dialogDecoration(label),
      );

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final lang = context.watch<LanguageProvider>();

    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 0, 14, 24),
      children: [
        TripCardExpanded(
          title: '💸 ${lang.translate('viagem.registerExpense')}',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: _formField(
                      label: lang.translate('expenses.value'),
                      child: TextField(
                        controller: _valorCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        style: const TextStyle(color: WebColors.text, fontSize: 14),
                        decoration: _fieldDecoration(hint: lang.translate('viagem.value.placeholder')),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    flex: 3,
                    child: _formField(
                      label: lang.translate('expenses.category'),
                      child: DropdownButtonFormField<String>(
                        initialValue: _categoria,
                        dropdownColor: WebColors.bg2,
                        style: const TextStyle(color: WebColors.text, fontSize: 13),
                        decoration: _fieldDecoration(),
                        items: Constants.categorias
                            .map((c) => DropdownMenuItem(
                                  value: c,
                                  child: Text('${Constants.categoriaEmoji[c] ?? ''} $c', style: const TextStyle(fontSize: 13)),
                                ))
                            .toList(),
                        onChanged: (v) => setState(() => _categoria = v ?? _categoria),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              _formField(
                label: lang.translate('expenses.description'),
                child: TextField(
                  controller: _descCtrl,
                  style: const TextStyle(color: WebColors.text, fontSize: 14),
                  decoration: _fieldDecoration(hint: lang.translate('expenses.descriptionHint')),
                ),
              ),
              const SizedBox(height: 12),
              _formField(
                label: lang.translate('expenses.date'),
                child: InkWell(
                  onTap: _pickDate,
                  borderRadius: BorderRadius.circular(WebColors.radiusSm),
                  child: Container(
                    height: 42,
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      color: WebColors.surface2,
                      borderRadius: BorderRadius.circular(WebColors.radiusSm),
                      border: Border.all(color: WebColors.border),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.calendar_today_outlined, size: 14, color: WebColors.textMuted),
                        const SizedBox(width: 8),
                        Text(
                          _dataGasto != null ? _dateFmt.format(_dataGasto!) : lang.translate('expenses.date'),
                          style: TextStyle(fontSize: 13, color: _dataGasto != null ? WebColors.text : WebColors.textMuted),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              if (_tripStart != null && _tripEnd != null) ...[
                const SizedBox(height: 4),
                Text(
                  '${lang.translate('expenses.dateRangeHint')} ${widget.dataInicioViagem} → ${widget.dataFimViagem}',
                  style: const TextStyle(fontSize: 11, color: WebColors.textMuted),
                ),
              ],
              if (widget.membros.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(lang.translate('expenses.splitWith'), style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: widget.membros.map((m) {
                    final sel = _selectedMembros.contains(m.id);
                    return FilterChip(
                      label: Text(m.nome.split(' ').first, style: const TextStyle(fontSize: 11)),
                      selected: sel,
                      onSelected: (v) => setState(() {
                        if (v) {
                          _selectedMembros.add(m.id);
                        } else {
                          _selectedMembros.remove(m.id);
                        }
                      }),
                      backgroundColor: WebColors.surface2,
                      selectedColor: WebColors.primary.withValues(alpha: 0.25),
                      checkmarkColor: WebColors.primary,
                      labelStyle: TextStyle(color: sel ? WebColors.primary : WebColors.textSecondary),
                      side: BorderSide(color: sel ? WebColors.primary : WebColors.border),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 4),
                Text(
                  _selectedMembros.isEmpty
                      ? lang.translate('expenses.splitNone').replaceFirst('{count}', widget.membros.length.toString())
                      : lang.translate('expenses.splitSelected').replaceFirst('{count}', _selectedMembros.length.toString()),
                  style: TextStyle(fontSize: 11, color: _selectedMembros.isEmpty ? WebColors.textMuted : WebColors.primary),
                ),
              ],
              const SizedBox(height: 14),
              GradientButton(
                onPressed: _saving ? null : _addGasto,
                child: SizedBox(
                  width: double.infinity,
                  child: Center(
                    child: _saving
                        ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text('+ ${lang.translate('viagem.registerBtn')}'),
                  ),
                ),
              ),
              if (_erro != null) ...[
                const SizedBox(height: 8),
                Text(_erro!, style: const TextStyle(color: WebColors.danger, fontSize: 12)),
              ],
            ],
          ),
        ),
        TripCardExpanded(
          title: lang.translate('viagem.history'),
          child: _loading
              ? const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator(color: WebColors.primary)))
              : _gastos.isEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        child: Text(lang.translate('viagem.emptyExpenses'), style: const TextStyle(color: WebColors.textMuted, fontSize: 14)),
                      ),
                    )
                  : Column(
                      children: _gastos.map((g) {
                        final isMe = g.idUsuario == widget.meId;
                        return CategoryItemRow(
                          left: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                g.descricao?.isNotEmpty == true ? g.descricao! : g.categoria,
                                style: const TextStyle(color: WebColors.text, fontSize: 14),
                              ),
                              Text('${g.categoria} · ${g.nomeUsuario} · ${g.dataGasto ?? ''}',
                                  style: const TextStyle(color: WebColors.textMuted, fontSize: 11)),
                            ],
                          ),
                          right: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text('R\$ ${g.valor.toStringAsFixed(2)}',
                                  style: const TextStyle(color: WebColors.success, fontWeight: FontWeight.w700, fontSize: 14)),
                              if (isMe) ...[
                                const SizedBox(width: 4),
                                IconButton(
                                  icon: const Icon(Icons.edit_outlined, size: 16, color: WebColors.textMuted),
                                  padding: const EdgeInsets.symmetric(horizontal: 2),
                                  constraints: const BoxConstraints(),
                                  onPressed: () => _editGasto(g),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.delete_outline, size: 16, color: WebColors.danger),
                                  padding: const EdgeInsets.symmetric(horizontal: 2),
                                  constraints: const BoxConstraints(),
                                  onPressed: () async {
                                    final ok = await confirmarAcao(
                                      context,
                                      titulo: lang.translate('viagem.confirmDeleteExpense'),
                                      mensagem: lang.translate('viagem.confirmDeleteExpenseBody'),
                                      textoConfirmar: lang.translate('common.delete'),
                                    );
                                    if (!ok) return;
                                    try {
                                      await GastoService.deletar(g.id);
                                      await _load();
                                      await widget.onReload();
                                    } catch (e) {
                                      if (context.mounted) {
                                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                                            content: Text(lang.translate('expenses.deleteError').replaceFirst('{error}', e.toString()))));
                                      }
                                    }
                                  },
                                ),
                              ],
                            ],
                          ),
                        );
                      }).toList(),
                    ),
        ),
      ],
    );
  }

  Widget _formField({required String label, required Widget child}) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
          const SizedBox(height: 4),
          child,
        ],
      );

  InputDecoration _fieldDecoration({String? hint}) => InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 13),
        filled: true,
        fillColor: WebColors.surface2,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(WebColors.radiusSm), borderSide: const BorderSide(color: WebColors.border)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(WebColors.radiusSm), borderSide: const BorderSide(color: WebColors.border)),
      );
}
