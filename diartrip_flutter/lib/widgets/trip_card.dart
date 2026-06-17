import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../models/grupo.dart';

class TripCard extends StatelessWidget {
  final Grupo grupo;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;

  const TripCard({
    super.key,
    required this.grupo,
    required this.onTap,
    this.onLongPress,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        onLongPress: onLongPress,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.flight_takeoff, color: AppTheme.primary, size: 24),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      grupo.nomeGrupo,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                        color: AppTheme.onSurface,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        const Icon(Icons.location_on, size: 13, color: AppTheme.onSurfaceMuted),
                        const SizedBox(width: 3),
                        Expanded(
                          child: Text(
                            grupo.destinoPrincipal,
                            style: const TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 13),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    if (grupo.dataInicio != null) ...[
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          const Icon(Icons.calendar_today, size: 12, color: AppTheme.onSurfaceMuted),
                          const SizedBox(width: 3),
                          Text(
                            _formatRange(grupo.dataInicio, grupo.dataFim),
                            style: const TextStyle(color: AppTheme.onSurfaceMuted, fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.auto_awesome, color: AppTheme.primary, size: 16),
                  const SizedBox(height: 6),
                  Icon(
                    Icons.info_outline,
                    color: AppTheme.onSurfaceMuted.withValues(alpha: 0.5),
                    size: 14,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatRange(String? inicio, String? fim) {
    if (inicio == null) return '';
    if (fim == null) return inicio;
    return '$inicio → $fim';
  }
}
