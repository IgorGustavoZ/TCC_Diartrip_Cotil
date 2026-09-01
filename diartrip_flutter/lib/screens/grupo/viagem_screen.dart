import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../core/app_logger.dart';
import '../../core/web_style.dart';
import '../../models/dashboard.dart';
import '../../models/grupo.dart';
import '../../providers/auth_provider.dart';
import '../../providers/language_provider.dart';
import '../../services/dashboard_service.dart';
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

/// Mirrors backend/frontend/lobby-pags/viagem.html: gradient `.trip-banner`
/// header + a wrapping pill `.tabs-nav`, above the same 7 tabs (Overview /
/// My Finances / Admin / Expenses / Itinerary / Chat / Info) — plus a
/// Photos tab, which has no web equivalent but is kept as a mobile-native
/// bonus (camera uploads), same precedent as elsewhere in the app. The
/// Admin tab is only present when the current member is actually admin,
/// matching `#adminTabBtn { display:none }` on the web.
class ViagemScreen extends StatefulWidget {
  final int idGrupo;
  /// Chave da aba inicial ('geral' por padrão, 'chat' vindo do deep link
  /// `/viagem/{id}?tab=chat`, equivalente a `viagem.html?id=X&tab=chat`).
  final String initialTab;
  const ViagemScreen({super.key, required this.idGrupo, this.initialTab = 'geral'});
  @override
  State<ViagemScreen> createState() => _ViagemScreenState();
}

class _ViagemScreenState extends State<ViagemScreen> with TickerProviderStateMixin {
  TabController? _tabCtrl;
  List<String> _tabKeys = [];
  Grupo? _grupo;
  List<Membro> _membros = [];
  DashboardCompleto? _dash;
  bool _loading = true;
  int _meId = 0;
  bool _isMeAdmin = false;

  /// Só a aba com este índice é de fato construída no `TabBarView` — as
  /// outras viram um placeholder vazio. Isso garante que sair de uma aba
  /// (Chat, por ex.) realmente derruba o websocket/timers/efeitos de blur
  /// dela, em vez de deixá-los rodando escondidos pra sempre: com todas as
  /// abas já visitadas permanecendo montadas ao mesmo tempo, o custo (várias
  /// conexões de rede + várias camadas de blur simultâneas) se acumulava até
  /// travar a interface depois de navegar por algumas abas.
  int _currentTabIndex = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _tabCtrl?.dispose();
    super.dispose();
  }

  void _onTabControllerChanged() {
    final i = _tabCtrl!.index;
    if (i != _currentTabIndex && mounted) {
      setState(() => _currentTabIndex = i);
    }
  }

  Future<void> _load() async {
    _meId = context.read<AuthProvider>().usuario?.id ?? 0;
    try {
      final results = await Future.wait([
        GrupoService.get(widget.idGrupo),
        GrupoService.listarMembros(widget.idGrupo),
        DashboardService.get(widget.idGrupo),
      ]);
      _grupo = results[0] as Grupo;
      _membros = results[1] as List<Membro>;
      _dash = results[2] as DashboardCompleto;
      _isMeAdmin = _membros.any((m) => m.id == _meId && m.isAdmin);
    } catch (e, s) {
      AppLogger.captureError('ViagemScreen._load', e, s);
    }
    _tabKeys = ['geral', 'pessoal', if (_isMeAdmin) 'admin', 'gastos', 'roteiro', 'fotos', 'chat', 'info'];
    if (_tabCtrl == null) {
      final idx = _tabKeys.indexOf(widget.initialTab);
      _currentTabIndex = idx >= 0 ? idx : 0;
      _tabCtrl = TabController(length: _tabKeys.length, vsync: this, initialIndex: _currentTabIndex)
        ..addListener(_onTabControllerChanged);
    } else if (_tabCtrl!.length != _tabKeys.length) {
      _currentTabIndex = _tabCtrl!.index.clamp(0, _tabKeys.length - 1);
      _tabCtrl!.dispose();
      _tabCtrl = TabController(length: _tabKeys.length, vsync: this, initialIndex: _currentTabIndex)
        ..addListener(_onTabControllerChanged);
    }
    if (mounted) setState(() => _loading = false);
  }


  void _copiarCodigo() {
    final codigo = _grupo?.codigoConvite;
    if (codigo == null) return;
    Clipboard.setData(ClipboardData(text: codigo));
    final lang = context.read<LanguageProvider>();
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(lang.translate('common.copied'))));
  }

  String _tabLabel(String key, LanguageProvider lang) {
    switch (key) {
      case 'geral':
        return lang.translate('viagem.tabs.overview');
      case 'pessoal':
        return lang.translate('viagem.tabs.finances');
      case 'admin':
        return lang.translate('viagem.tabs.admin');
      case 'gastos':
        return lang.translate('viagem.tabs.expenses');
      case 'roteiro':
        return lang.translate('viagem.tabs.itinerary');
      case 'fotos':
        return lang.translate('viagem.tabs.photos');
      case 'chat':
        return lang.translate('viagem.tabs.chat');
      case 'info':
        return lang.translate('viagem.tabs.info');
      default:
        return key;
    }
  }

  /// Mesmos emojis dos botões de aba em viagem.html (`📊 Overview`, `👤 My
  /// Finances`, `👑 Admin`...) — Fotos não existe no site, então ganha um
  /// emoji equivalente (📷) só pra manter o mesmo padrão visual.
  String _tabEmoji(String key) {
    switch (key) {
      case 'geral':
        return '📊';
      case 'pessoal':
        return '👤';
      case 'admin':
        return '👑';
      case 'gastos':
        return '💸';
      case 'roteiro':
        return '📋';
      case 'fotos':
        return '📷';
      case 'chat':
        return '💬';
      case 'info':
        return '📌';
      default:
        return '';
    }
  }

  Widget _tabView(String key) {
    switch (key) {
      case 'geral':
        return OverviewTab(dash: _dash, onReload: _load);
      case 'pessoal':
        return FinancesTab(idGrupo: widget.idGrupo, dash: _dash, onReload: _load);
      case 'admin':
        return AdminTab(
          idGrupo: widget.idGrupo,
          grupo: _grupo!,
          dash: _dash,
          membros: _membros,
          meId: _meId,
          isAdmin: _isMeAdmin,
          onReload: _load,
        );
      case 'gastos':
        return ExpensesTab(
          idGrupo: widget.idGrupo,
          meId: _meId,
          membros: _membros,
          dataInicioViagem: _grupo?.dataInicio,
          dataFimViagem: _grupo?.dataFim,
          onReload: _load,
        );
      case 'roteiro':
        return ItineraryTab(idGrupo: widget.idGrupo, isAdmin: _isMeAdmin, onReload: _load);
      case 'fotos':
        return PhotosTab(idGrupo: widget.idGrupo, meId: _meId, onReload: _load);
      case 'chat':
        return ChatTab(idGrupo: widget.idGrupo, meId: _meId, membros: _membros);
      case 'info':
        return InfoTab(grupo: _grupo!, meId: _meId, onReload: _load);
      default:
        return const SizedBox.shrink();
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return Scaffold(
      backgroundColor: WebColors.bg,
      drawer: AppDrawer(activeRoute: '/viagem/${widget.idGrupo}'),
      appBar: AppBar(
        backgroundColor: WebColors.bg,
        elevation: 0,
        iconTheme: const IconThemeData(color: WebColors.textSecondary),
        title: Text(
          _grupo?.nomeGrupo ?? lang.translate('viagem.title'),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 17),
        ),
      ),
      body: Stack(
        children: [
          const Positioned.fill(child: AmbientBackground()),
          SafeArea(
            top: false,
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: WebColors.primary))
                : _grupo == null
                    ? _erroState(lang)
                    : Column(
                        children: [
                          Padding(
                            padding: const EdgeInsets.fromLTRB(14, 14, 14, 0),
                            child: Column(
                              children: [
                                _tripBanner(lang),
                                const SizedBox(height: 14),
                                _tabsNav(lang),
                                const SizedBox(height: 14),
                              ],
                            ),
                          ),
                          Expanded(
                            // Sem arrastar pra trocar de aba: só a aba atual
                            // existe de verdade no momento (as outras são um
                            // placeholder vazio), então um gesto de swipe
                            // mostraria uma página em branco no meio da
                            // transição. A troca continua funcionando
                            // normalmente pelos botões da navegação acima.
                            child: TabBarView(
                              controller: _tabCtrl,
                              physics: const NeverScrollableScrollPhysics(),
                              children: List.generate(
                                _tabKeys.length,
                                (i) => i == _currentTabIndex ? _tabView(_tabKeys[i]) : const SizedBox.shrink(),
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

  Widget _erroState(LanguageProvider lang) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.wifi_off_outlined, size: 48, color: WebColors.textMuted),
          const SizedBox(height: 12),
          Text(lang.translate('viagem.error'), style: const TextStyle(color: WebColors.textMuted)),
          const SizedBox(height: 16),
          OutlinedButton(
            onPressed: _load,
            style: OutlinedButton.styleFrom(
              foregroundColor: WebColors.textSecondary,
              side: const BorderSide(color: WebColors.borderStrong),
            ),
            child: Text(lang.translate('viagem.retry')),
          ),
        ],
      ),
    );
  }

  Widget _tripBanner(LanguageProvider lang) {
    final g = _grupo!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: WebColors.gradient,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: WebColors.primary.withValues(alpha: 0.28), blurRadius: 32, offset: const Offset(0, 14)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(g.nomeGrupo,
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 22)),
          const SizedBox(height: 6),
          Text('📍 ${g.destinoPrincipal}',
              style: TextStyle(color: Colors.white.withValues(alpha: 0.92), fontSize: 14)),
          if (g.dataInicio != null) ...[
            const SizedBox(height: 2),
            Text('${g.dataInicio} → ${g.dataFim ?? ''}',
                style: TextStyle(color: Colors.white.withValues(alpha: 0.75), fontSize: 12)),
          ],
          if (g.codigoConvite != null) ...[
            const SizedBox(height: 14),
            Material(
              color: Colors.white.withValues(alpha: 0.18),
              borderRadius: BorderRadius.circular(WebColors.radiusMd),
              child: InkWell(
                borderRadius: BorderRadius.circular(WebColors.radiusMd),
                onTap: _copiarCodigo,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(WebColors.radiusMd),
                    border: Border.all(color: Colors.white.withValues(alpha: 0.4)),
                  ),
                  child: Text(lang.translate('viagem.copyCode'),
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _tabsNav(LanguageProvider lang) {
    return GlassContainer(
      padding: const EdgeInsets.all(10),
      child: AnimatedBuilder(
        animation: _tabCtrl!,
        builder: (context, _) => Wrap(
          alignment: WrapAlignment.center,
          spacing: 8,
          runSpacing: 8,
          children: List.generate(_tabKeys.length, (i) {
            final key = _tabKeys[i];
            final active = _tabCtrl!.index == i;
            return _tabBtn(_tabEmoji(key), _tabLabel(key, lang), active, () => _tabCtrl!.animateTo(i));
          }),
        ),
      ),
    );
  }

  Widget _tabBtn(String emoji, String label, bool active, VoidCallback onTap) {
    return Material(
      color: active ? Colors.transparent : WebColors.surface2,
      borderRadius: BorderRadius.circular(WebColors.radiusPill),
      child: InkWell(
        borderRadius: BorderRadius.circular(WebColors.radiusPill),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
          decoration: BoxDecoration(
            gradient: active ? WebColors.gradient : null,
            borderRadius: BorderRadius.circular(WebColors.radiusPill),
            border: active ? null : Border.all(color: WebColors.border),
            boxShadow: active
                ? [BoxShadow(color: WebColors.primary.withValues(alpha: 0.35), blurRadius: 14, offset: const Offset(0, 5))]
                : null,
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(emoji, style: const TextStyle(fontSize: 13)),
              const SizedBox(width: 6),
              Text(label,
                  style: TextStyle(
                    color: active ? Colors.white : WebColors.textSecondary,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  )),
            ],
          ),
        ),
      ),
    );
  }
}
