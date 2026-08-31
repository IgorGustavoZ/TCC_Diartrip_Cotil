import 'package:flutter/material.dart';
import '../core/app_logger.dart';
import '../core/web_style.dart';
import '../models/grupo.dart';
import '../services/dashboard_service.dart';

/// Trip card matching `.trip-card`/`.trip-cover`/`.trip-card-body` in
/// backend/frontend/style.css: glass surface, gradient cover with an emoji,
/// name/destination/dates, and a best-effort budget bar (same silent-failure
/// enrichment as `enriquecerOrcamento()` in lobby.html).
class TripCard extends StatefulWidget {
  final Grupo grupo;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;
  final bool selected;

  const TripCard({
    super.key,
    required this.grupo,
    required this.onTap,
    this.onLongPress,
    this.selected = false,
  });

  @override
  State<TripCard> createState() => _TripCardState();
}

class _TripCardState extends State<TripCard> {
  double? _orcamentoTotal;
  int? _percentual;

  @override
  void initState() {
    super.initState();
    _carregarOrcamento();
  }

  Future<void> _carregarOrcamento() async {
    try {
      final geral = await DashboardService.geral(widget.grupo.id);
      if (mounted && geral.orcamentoTotal > 0) {
        setState(() {
          _orcamentoTotal = geral.orcamentoTotal;
          _percentual = geral.percentualConsumido.clamp(0, 100);
        });
      }
    } catch (e) {
      // Enriquecimento best-effort — igual a enriquecerOrcamento() em lobby.html:
      // card continua útil sem a barra de orçamento, sem reportar como erro.
      AppLogger.info('TripCard._carregarOrcamento', '$e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final g = widget.grupo;
    return GlassContainer(
      radius: WebColors.radiusLg,
      color: widget.selected ? WebColors.primary.withValues(alpha: 0.10) : null,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: widget.onTap,
          onLongPress: widget.onLongPress,
          borderRadius: BorderRadius.circular(WebColors.radiusLg),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(WebColors.radiusLg),
              border: widget.selected ? Border.all(color: WebColors.primary, width: 2) : null,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  height: 92,
                  decoration: BoxDecoration(
                    gradient: tripCoverGradientFor(g.destinoPrincipal),
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(WebColors.radiusLg)),
                  ),
                  alignment: Alignment.bottomRight,
                  padding: const EdgeInsets.only(right: 14, bottom: 10),
                  child: const Text('✈️', style: TextStyle(fontSize: 26)),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 16, 18, 18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        g.nomeGrupo,
                        style: const TextStyle(color: WebColors.text, fontSize: 16, fontWeight: FontWeight.w700),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 5),
                      Text(
                        '📍 ${g.destinoPrincipal}',
                        style: const TextStyle(color: WebColors.textMuted, fontSize: 13),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (g.dataInicio != null) ...[
                        const SizedBox(height: 3),
                        Text(
                          '🗓 ${g.dataInicio} — ${g.dataFim ?? ''}',
                          style: const TextStyle(color: WebColors.textMuted, fontSize: 13),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                      if (_orcamentoTotal != null) ...[
                        const SizedBox(height: 10),
                        Text(
                          'R\$ ${_orcamentoTotal!.toStringAsFixed(2)} · $_percentual%',
                          style: const TextStyle(color: WebColors.textMuted, fontSize: 12),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(WebColors.radiusPill),
                          child: LinearProgressIndicator(
                            value: (_percentual ?? 0) / 100,
                            minHeight: 6,
                            backgroundColor: WebColors.surface2,
                            valueColor: const AlwaysStoppedAnimation(WebColors.accent),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
