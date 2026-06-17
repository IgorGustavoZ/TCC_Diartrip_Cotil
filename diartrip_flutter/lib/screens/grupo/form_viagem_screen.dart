import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/constants.dart';
import '../../providers/language_provider.dart';
import '../../services/grupo_service.dart';

class FormViagemScreen extends StatefulWidget {
  const FormViagemScreen({super.key});
  @override
  State<FormViagemScreen> createState() => _FormViagemScreenState();
}

class _FormViagemScreenState extends State<FormViagemScreen> {
  final _form = GlobalKey<FormState>();
  final _nomeCtrl = TextEditingController();
  final _destinoCtrl = TextEditingController();
  final _orcamentoCtrl = TextEditingController();
  final _prefsCtrl = TextEditingController();
  DateTime? _dataInicio;
  DateTime? _dataFim;
  String _tipoViagem = 'Lazer';
  bool _loading = false;
  String? _erro;
  final _fmt = DateFormat('yyyy-MM-dd');

  @override
  void dispose() {
    _nomeCtrl.dispose();
    _destinoCtrl.dispose();
    _orcamentoCtrl.dispose();
    _prefsCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDate(bool isInicio) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: (isInicio ? _dataInicio : _dataFim) ?? now,
      firstDate: now,
      lastDate: DateTime(now.year + 5),
    );
    if (picked == null) return;
    setState(() {
      if (isInicio) {
        _dataInicio = picked;
        if (_dataFim != null && _dataFim!.isBefore(picked)) _dataFim = null;
      } else {
        _dataFim = picked;
      }
    });
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    if (_dataInicio == null || _dataFim == null) {
      setState(() => _erro = context.read<LanguageProvider>().translate('formViagem.selectDates'));
      return;
    }
    setState(() { _erro = null; _loading = true; });
    try {
      final idGrupo = await GrupoService.criar(
        nomeGrupo: _nomeCtrl.text.trim(),
        destinoPrincipal: _destinoCtrl.text.trim(),
        dataInicio: _fmt.format(_dataInicio!),
        dataFim: _fmt.format(_dataFim!),
        orcamento: double.tryParse(_orcamentoCtrl.text.replaceAll(',', '.')) ?? 0,
        tipoViagem: _tipoViagem,
        preferencias: _prefsCtrl.text.trim(),
      );
      if (mounted) Navigator.pushReplacementNamed(context, '/viagem/$idGrupo');
    } catch (e) {
      setState(() => _erro = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return Scaffold(
      appBar: AppBar(title: Text(lang.translate('lobby.newTrip'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _form,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _nomeCtrl,
                decoration: InputDecoration(
                  labelText: lang.translate('formViagem.tripName'),
                  prefixIcon: const Icon(Icons.luggage_outlined),
                ),
                validator: (v) => v != null && v.trim().isNotEmpty
                    ? null : lang.translate('formViagem.required'),
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _destinoCtrl,
                decoration: InputDecoration(
                  labelText: lang.translate('formViagem.destination'),
                  prefixIcon: const Icon(Icons.location_on_outlined),
                ),
                validator: (v) => v != null && v.trim().isNotEmpty
                    ? null : lang.translate('formViagem.required'),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(child: _datePicker(lang.translate('formViagem.startDate'), _dataInicio, () => _pickDate(true))),
                  const SizedBox(width: 12),
                  Expanded(child: _datePicker(lang.translate('formViagem.endDate'), _dataFim, () => _pickDate(false))),
                ],
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _orcamentoCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: lang.translate('formViagem.budget'),
                  prefixIcon: const Icon(Icons.attach_money),
                ),
                validator: (v) {
                  if (v == null || v.isEmpty) return lang.translate('formViagem.required');
                  if (double.tryParse(v.replaceAll(',', '.')) == null) return lang.translate('formViagem.invalidValue');
                  return null;
                },
              ),
              const SizedBox(height: 14),
              DropdownMenu<String>(
                initialSelection: _tipoViagem,
                label: Text(lang.translate('formViagem.tripType')),
                leadingIcon: const Icon(Icons.category_outlined, size: 18),
                expandedInsets: EdgeInsets.zero,
                dropdownMenuEntries: Constants.tiposViagem
                    .map((t) => DropdownMenuEntry(value: t, label: t))
                    .toList(),
                onSelected: (v) => setState(() => _tipoViagem = v ?? _tipoViagem),
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _prefsCtrl,
                maxLines: 3,
                decoration: InputDecoration(
                  labelText: lang.translate('formViagem.preferences'),
                  prefixIcon: const Icon(Icons.favorite_outline),
                  alignLabelWithHint: true,
                ),
              ),
              if (_erro != null) ...[
                const SizedBox(height: 12),
                Text(_erro!, style: const TextStyle(color: Colors.red, fontSize: 13)),
              ],
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _loading ? null : _submit,
                child: _loading
                    ? const SizedBox(
                        height: 18, width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : Text(lang.translate('formViagem.createBtn')),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _datePicker(String label, DateTime? date, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
        decoration: BoxDecoration(
          color: Theme.of(context).inputDecorationTheme.fillColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        ),
        child: Row(
          children: [
            const Icon(Icons.calendar_today, size: 16, color: Colors.grey),
            const SizedBox(width: 8),
            Text(
              date != null ? _fmt.format(date) : label,
              style: TextStyle(
                color: date != null ? Colors.white : Colors.grey,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
