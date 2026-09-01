import 'package:flutter/material.dart';
import '../core/web_style.dart';
import '../models/grupo.dart';
import '../providers/language_provider.dart';

/// `.next-trip` banner: gradient card highlighting the closest upcoming
/// trip, mirroring `renderNextTrip()` in backend/frontend/lobby.html.
class NextTripBanner extends StatelessWidget {
  final Grupo grupo;
  final LanguageProvider lang;
  final VoidCallback onTap;

  const NextTripBanner({super.key, required this.grupo, required this.lang, required this.onTap});

  /// Nearest trip whose start date hasn't passed yet, or null if none.
  static Grupo? proxima(List<Grupo> grupos) {
    final hoje = DateTime.now();
    final hojeSemHora = DateTime(hoje.year, hoje.month, hoje.day);

    final futuras = grupos.where((g) {
      if (g.dataInicio == null) return false;
      final d = DateTime.tryParse(g.dataInicio!);
      return d != null && !d.isBefore(hojeSemHora);
    }).toList()
      ..sort((a, b) => a.dataInicio!.compareTo(b.dataInicio!));

    return futuras.isEmpty ? null : futuras.first;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 22),
      decoration: BoxDecoration(
        gradient: WebColors.gradient,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: WebColors.primary.withValues(alpha: 0.28), blurRadius: 28, offset: const Offset(0, 12)),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '✈ ${lang.translate('lobby.nextTrip.label').toUpperCase()}',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.85),
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.6,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  grupo.nomeGrupo,
                  style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  '📍 ${grupo.destinoPrincipal} · ${grupo.dataInicio ?? ''} — ${grupo.dataFim ?? ''}',
                  style: TextStyle(color: Colors.white.withValues(alpha: 0.92), fontSize: 13),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Material(
            color: Colors.white.withValues(alpha: 0.18),
            borderRadius: BorderRadius.circular(WebColors.radiusMd),
            child: InkWell(
              borderRadius: BorderRadius.circular(WebColors.radiusMd),
              onTap: onTap,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(WebColors.radiusMd),
                  border: Border.all(color: Colors.white.withValues(alpha: 0.4)),
                ),
                child: Text(
                  lang.translate('grupos.openTrip'),
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
