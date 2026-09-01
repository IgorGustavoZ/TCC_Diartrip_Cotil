import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/api_client.dart';
import '../../core/web_style.dart';
import '../../models/viagem_explorar.dart';
import '../../providers/auth_provider.dart';
import '../../providers/language_provider.dart';
import '../../services/explorar_viagens_service.dart';
import '../../widgets/app_drawer.dart';

/// Mirrors backend/frontend/lobby-pags/explorar-viagens.html: search public
/// trips by destination and request to join one (optional message + budget).
class ExplorarViagensScreen extends StatefulWidget {
  const ExplorarViagensScreen({super.key});
  @override
  State<ExplorarViagensScreen> createState() => _ExplorarViagensScreenState();
}

class _ExplorarViagensScreenState extends State<ExplorarViagensScreen> {
  final _destinoCtrl = TextEditingController();
  List<ViagemExplorar> _viagens = [];
  bool _loading = true;
  String? _erro;

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  @override
  void dispose() {
    _destinoCtrl.dispose();
    super.dispose();
  }

  Future<void> _carregar() async {
    final lang = context.read<LanguageProvider>();
    setState(() { _loading = true; _erro = null; });
    try {
      final v = await ExplorarViagensService.listar(destino: _destinoCtrl.text.trim());
      if (mounted) setState(() { _viagens = v; _loading = false; });
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _erro = e is ApiException ? e.message : lang.translate('feed.loadError');
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final me = context.watch<AuthProvider>().usuario;
    final lang = context.watch<LanguageProvider>();
    return Scaffold(
      backgroundColor: WebColors.bg,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: const Color(0xB80B1220),
        elevation: 0,
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
            child: const SizedBox.expand(),
          ),
        ),
        iconTheme: const IconThemeData(color: WebColors.textSecondary),
        title: Text(
          lang.translate('explorar.header'),
          style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 18),
        ),
      ),
      drawer: const AppDrawer(activeRoute: '/explorar'),
      body: Stack(
        children: [
          const Positioned.fill(child: AmbientBackground()),
          SafeArea(
            child: RefreshIndicator(
              onRefresh: _carregar,
              color: WebColors.primary,
              backgroundColor: WebColors.bg,
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 720),
                  child: ListView(
                    padding: EdgeInsets.fromLTRB(14, kToolbarHeight + 4, 14, 24),
                    children: [
                      _buscaCard(lang),
                      const SizedBox(height: 16),
                      if (_loading)
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 48),
                          child: Center(child: CircularProgressIndicator(color: WebColors.primary)),
                        )
                      else if (_erro != null)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 32),
                          child: Center(
                            child: Column(
                              children: [
                                const Icon(Icons.wifi_off, size: 40, color: WebColors.textMuted),
                                const SizedBox(height: 10),
                                Text(_erro!, style: const TextStyle(color: WebColors.textMuted), textAlign: TextAlign.center),
                                const SizedBox(height: 10),
                                TextButton(onPressed: _carregar, child: Text(lang.translate('feed.retry'))),
                              ],
                            ),
                          ),
                        )
                      else if (_viagens.isEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 48),
                          child: Center(
                            child: Text(lang.translate('explorar.empty'), style: const TextStyle(color: WebColors.textMuted)),
                          ),
                        )
                      else
                        for (final v in _viagens) ...[
                          _ExplorarCard(viagem: v, meuId: me?.id ?? 0),
                          const SizedBox(height: 14),
                        ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buscaCard(LanguageProvider lang) {
    return GlassContainer(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Expanded(
            child: Container(
              height: 44,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: WebColors.surface2,
                borderRadius: BorderRadius.circular(WebColors.radiusMd),
                border: Border.all(color: WebColors.border),
              ),
              child: TextField(
                controller: _destinoCtrl,
                style: const TextStyle(color: WebColors.text, fontSize: 14),
                decoration: InputDecoration(
                  filled: false,
                  border: InputBorder.none,
                  enabledBorder: InputBorder.none,
                  focusedBorder: InputBorder.none,
                  isCollapsed: true,
                  hintText: lang.translate('explorar.searchPlaceholder'),
                  hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 14),
                ),
                onSubmitted: (_) => _carregar(),
              ),
            ),
          ),
          const SizedBox(width: 10),
          GradientButton(
            radius: WebColors.radiusMd,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            onPressed: _carregar,
            child: Text(lang.translate('explorar.searchBtn'), style: const TextStyle(fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

class _ExplorarCard extends StatefulWidget {
  final ViagemExplorar viagem;
  final int meuId;
  const _ExplorarCard({required this.viagem, required this.meuId});

  @override
  State<_ExplorarCard> createState() => _ExplorarCardState();
}

class _ExplorarCardState extends State<_ExplorarCard> {
  bool _showForm = false;
  bool _sending = false;
  bool _sent = false;
  String? _feedback;
  bool _feedbackErro = false;
  final _msgCtrl = TextEditingController();
  final _orcamentoCtrl = TextEditingController();
  final _msgFocus = FocusNode();

  @override
  void dispose() {
    _msgCtrl.dispose();
    _orcamentoCtrl.dispose();
    _msgFocus.dispose();
    super.dispose();
  }

  void _toggleForm() {
    setState(() => _showForm = !_showForm);
    if (_showForm) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _msgFocus.requestFocus());
    }
  }

  Future<void> _enviar() async {
    final lang = context.read<LanguageProvider>();
    setState(() => _feedback = null);

    double? orcamento;
    final orcTxt = _orcamentoCtrl.text.trim();
    if (orcTxt.isNotEmpty) {
      orcamento = double.tryParse(orcTxt.replaceAll(',', '.'));
      if (orcamento == null || orcamento < 0) {
        setState(() { _feedback = lang.translate('explorar.invalidBudget'); _feedbackErro = true; });
        return;
      }
    }

    setState(() => _sending = true);
    try {
      await ExplorarViagensService.solicitar(
        widget.viagem.id,
        mensagem: _msgCtrl.text.trim().isEmpty ? null : _msgCtrl.text.trim(),
        orcamento: orcamento,
      );
      if (!mounted) return;
      setState(() {
        _feedback = lang.translate('explorar.requestSent');
        _feedbackErro = false;
        _sent = true;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _feedback = e is ApiException ? e.message : lang.translate('explorar.requestError');
          _feedbackErro = true;
        });
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    final v = widget.viagem;
    final minhaViagem = v.idCriador == widget.meuId;

    return GlassContainer(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('✈️ ${v.nomeGrupo}', style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 16)),
          const SizedBox(height: 4),
          Text('${lang.translate('explorar.createdBy')} ${v.criador}',
              style: const TextStyle(color: WebColors.textMuted, fontSize: 12)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 16,
            runSpacing: 4,
            children: [
              if (v.destinoPrincipal != null && v.destinoPrincipal!.isNotEmpty)
                _meta('📍 ${v.destinoPrincipal}'),
              if (v.dataInicio != null && v.dataFim != null)
                _meta('📅 ${v.dataInicio} → ${v.dataFim}'),
              _meta(
                '👥 ${v.vagasOcupadas}/${v.limiteParticipantes} ${lang.translate('explorar.participants')}',
                color: v.cheia ? WebColors.danger : WebColors.textSecondary,
                bold: true,
              ),
              if (v.orcamentoTotal != null)
                _meta('💰 ${lang.translate('explorar.budgetTotal')}: R\$ ${v.orcamentoTotal!.toStringAsFixed(2)}'),
            ],
          ),
          const SizedBox(height: 14),
          if (minhaViagem)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
              decoration: BoxDecoration(
                color: WebColors.surface2,
                border: Border.all(color: WebColors.border),
                borderRadius: BorderRadius.circular(WebColors.radiusMd),
              ),
              child: Text(lang.translate('explorar.ownTrip'),
                  style: const TextStyle(color: WebColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
            )
          else
            GradientButton(
              radius: WebColors.radiusMd,
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 9),
              onPressed: v.cheia ? null : _toggleForm,
              child: Text(
                v.cheia ? lang.translate('explorar.full') : lang.translate('explorar.viewTrip'),
                style: const TextStyle(fontSize: 13),
              ),
            ),
          if (_showForm && !minhaViagem) ...[
            const SizedBox(height: 14),
            _campo(
              controller: _msgCtrl,
              focusNode: _msgFocus,
              hint: lang.translate('explorar.requestMessagePlaceholder'),
              maxLines: 2,
              enabled: !_sent,
            ),
            const SizedBox(height: 8),
            Text(lang.translate('explorar.myBudget'), style: const TextStyle(color: WebColors.textSecondary, fontSize: 12, fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            _campo(
              controller: _orcamentoCtrl,
              hint: lang.translate('explorar.myBudgetPlaceholder'),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              enabled: !_sent,
            ),
            const SizedBox(height: 8),
            GradientButton(
              radius: WebColors.radiusMd,
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 9),
              onPressed: _sent || _sending ? null : _enviar,
              child: _sending
                  ? const SizedBox(height: 14, width: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : Text(lang.translate('explorar.requestSend'), style: const TextStyle(fontSize: 13)),
            ),
            if (_feedback != null) ...[
              const SizedBox(height: 6),
              Text(_feedback!, style: TextStyle(color: _feedbackErro ? WebColors.danger : WebColors.success, fontSize: 12)),
            ],
          ],
        ],
      ),
    );
  }

  Widget _meta(String text, {Color color = WebColors.textSecondary, bool bold = false}) {
    return Text(text, style: TextStyle(color: color, fontSize: 13, fontWeight: bold ? FontWeight.w600 : FontWeight.normal));
  }

  Widget _campo({
    required TextEditingController controller,
    FocusNode? focusNode,
    required String hint,
    int maxLines = 1,
    TextInputType? keyboardType,
    bool enabled = true,
  }) {
    return TextField(
      controller: controller,
      focusNode: focusNode,
      maxLines: maxLines,
      keyboardType: keyboardType,
      enabled: enabled,
      style: const TextStyle(color: WebColors.text, fontSize: 13),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: WebColors.textMuted, fontSize: 13),
        filled: true,
        fillColor: WebColors.surface2,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(WebColors.radiusSm), borderSide: BorderSide.none),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(WebColors.radiusSm),
          borderSide: const BorderSide(color: WebColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(WebColors.radiusSm),
          borderSide: const BorderSide(color: WebColors.primary),
        ),
      ),
    );
  }
}
