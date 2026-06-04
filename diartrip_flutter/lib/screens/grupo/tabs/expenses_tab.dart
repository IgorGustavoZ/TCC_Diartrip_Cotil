import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/app_logger.dart';
import '../../../core/constants.dart';
import '../../../core/theme.dart';
import '../../../models/gasto.dart';
import '../../../models/grupo.dart';
import '../../../services/gasto_service.dart';

class ExpensesTab extends StatefulWidget {
  final int idGrupo;
  final int meId;
  final List<Membro> membros;

  const ExpensesTab({
    super.key,
    required this.idGrupo,
    required this.meId,
    required this.membros,
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

  static final _dateFmt = DateFormat('yyyy-MM-dd');

  @override
  void initState() {
    super.initState();
    _load();
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
    final picked = await showDatePicker(
      context: context,
      initialDate: _dataGasto ?? now,
      firstDate: DateTime(now.year - 2),
      lastDate: now,
    );
    if (picked != null) setState(() => _dataGasto = picked);
  }

  Future<void> _addGasto() async {
    final valor = double.tryParse(_valorCtrl.text.replaceAll(',', '.'));
    if (valor == null || valor <= 0) return;
    setState(() => _saving = true);
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
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _editGasto(Gasto gasto) async {
    final valorCtrl =
        TextEditingController(text: gasto.valor.toStringAsFixed(2));
    final descCtrl = TextEditingController(text: gasto.descricao ?? '');
    var cat = gasto.categoria;
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (ctx, setDialog) => AlertDialog(
          title: const Text('Edit Expense'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: valorCtrl,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Value (R\$)',
                  prefixIcon: Icon(Icons.attach_money, size: 18),
                ),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                initialValue: cat,
                decoration: const InputDecoration(labelText: 'Category'),
                items: Constants.categorias
                    .map((c) => DropdownMenuItem(
                          value: c,
                          child: Text(
                              '${Constants.categoriaEmoji[c] ?? ''} $c'),
                        ))
                    .toList(),
                onChanged: (v) => setDialog(() => cat = v ?? cat),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: descCtrl,
                decoration: const InputDecoration(labelText: 'Description'),
              ),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('Cancel')),
            ElevatedButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('Save')),
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
      _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return Column(
      children: [
        Container(
          color: AppTheme.surface,
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: TextField(
                      controller: _valorCtrl,
                      keyboardType:
                          const TextInputType.numberWithOptions(decimal: true),
                      decoration: const InputDecoration(
                        labelText: 'Value (R\$)',
                        prefixIcon: Icon(Icons.attach_money, size: 18),
                        contentPadding:
                            EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    flex: 3,
                    child: DropdownButtonFormField<String>(
                      initialValue: _categoria,
                      decoration: const InputDecoration(
                        contentPadding:
                            EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      ),
                      items: Constants.categorias
                          .map((c) => DropdownMenuItem(
                                value: c,
                                child: Text(
                                    '${Constants.categoriaEmoji[c] ?? ''} $c',
                                    style: const TextStyle(fontSize: 13)),
                              ))
                          .toList(),
                      onChanged: (v) =>
                          setState(() => _categoria = v ?? _categoria),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _descCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Description (optional)',
                        contentPadding:
                            EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: _pickDate,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 10),
                      decoration: BoxDecoration(
                        color: AppTheme.surfaceVariant,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                            color: Colors.white.withValues(alpha: 0.08)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.calendar_today,
                              size: 14, color: AppTheme.onSurfaceMuted),
                          const SizedBox(width: 4),
                          Text(
                            _dataGasto != null
                                ? _dateFmt.format(_dataGasto!)
                                : 'Date',
                            style: TextStyle(
                              fontSize: 12,
                              color: _dataGasto != null
                                  ? AppTheme.onSurface
                                  : AppTheme.onSurfaceMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              if (widget.membros.isNotEmpty) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  children: [
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 4),
                      child: Text('Split with:',
                          style: TextStyle(
                              color: AppTheme.onSurfaceMuted, fontSize: 12)),
                    ),
                    ...widget.membros.map((m) {
                      final sel = _selectedMembros.contains(m.id);
                      return FilterChip(
                        label: Text(m.nome.split(' ').first,
                            style: const TextStyle(fontSize: 11)),
                        selected: sel,
                        onSelected: (v) => setState(() {
                          if (v) {
                            _selectedMembros.add(m.id);
                          } else {
                            _selectedMembros.remove(m.id);
                          }
                        }),
                        selectedColor:
                            AppTheme.primary.withValues(alpha: 0.25),
                        checkmarkColor: AppTheme.primary,
                        padding: const EdgeInsets.symmetric(horizontal: 6),
                        labelPadding: EdgeInsets.zero,
                      );
                    }),
                  ],
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Text(
                    _selectedMembros.isEmpty
                        ? 'No one selected → split equally among all ${widget.membros.length} members'
                        : 'Splitting among ${_selectedMembros.length} selected member(s)',
                    style: TextStyle(
                      fontSize: 11,
                      color: _selectedMembros.isEmpty
                          ? AppTheme.onSurfaceMuted
                          : AppTheme.primary,
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _saving ? null : _addGasto,
                  style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 10)),
                  child: _saving
                      ? const SizedBox(
                          height: 14,
                          width: 14,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Add Expense'),
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : RefreshIndicator(
                  onRefresh: _load,
                  child: _gastos.isEmpty
                      ? const Center(
                          child: Text('No expenses yet.',
                              style:
                                  TextStyle(color: AppTheme.onSurfaceMuted)))
                      : ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _gastos.length,
                          itemBuilder: (_, i) {
                            final g = _gastos[i];
                            final isMe = g.idUsuario == widget.meId;
                            return Card(
                              child: ListTile(
                                leading: Text(
                                    Constants.categoriaEmoji[g.categoria] ??
                                        '📦',
                                    style: const TextStyle(fontSize: 22)),
                                title: Text(
                                  g.descricao?.isNotEmpty == true
                                      ? g.descricao!
                                      : g.categoria,
                                  style: const TextStyle(fontSize: 14),
                                ),
                                subtitle: Text(
                                  '${g.nomeUsuario} · ${g.dataGasto ?? ''}',
                                  style: const TextStyle(fontSize: 12),
                                ),
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text(
                                        'R\$ ${g.valor.toStringAsFixed(2)}',
                                        style: const TextStyle(
                                            fontWeight: FontWeight.w600)),
                                    if (isMe) ...[
                                      IconButton(
                                        icon: const Icon(
                                            Icons.edit_outlined,
                                            size: 16),
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 4),
                                        constraints: const BoxConstraints(),
                                        onPressed: () => _editGasto(g),
                                      ),
                                      IconButton(
                                        icon: const Icon(
                                            Icons.delete_outline,
                                            size: 16,
                                            color: AppTheme.error),
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 4),
                                        constraints: const BoxConstraints(),
                                        onPressed: () async {
                                          try {
                                            await GastoService.deletar(g.id);
                                            await _load();
                                          } catch (e) {
                                            if (context.mounted) {
                                              ScaffoldMessenger.of(context)
                                                  .showSnackBar(SnackBar(
                                                      content: Text(
                                                          'Erro ao deletar gasto: $e')));
                                            }
                                          }
                                        },
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                ),
        ),
      ],
    );
  }
}
