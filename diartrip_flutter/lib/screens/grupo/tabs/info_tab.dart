import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../core/theme.dart';
import '../../../models/grupo.dart';

class InfoTab extends StatelessWidget {
  final Grupo grupo;
  const InfoTab({super.key, required this.grupo});

  static const _aiTips = [
    '"What are the best restaurants in [destination]?"',
    '"Suggest a 3-day itinerary for our trip."',
    '"What should we pack for this type of trip?"',
    '"How can we split costs fairly among the group?"',
    '"What are must-see attractions near [destination]?"',
    '"Any local customs or tips we should know?"',
  ];

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Icon(Icons.flight_takeoff, size: 48, color: AppTheme.primary),
        const SizedBox(height: 12),
        Text(grupo.nomeGrupo,
            textAlign: TextAlign.center,
            style: const TextStyle(
                fontSize: 20, fontWeight: FontWeight.w700)),
        const SizedBox(height: 20),
        _infoRow(Icons.location_on_outlined, 'Destination',
            grupo.destinoPrincipal),
        if (grupo.dataInicio != null)
          _infoRow(Icons.calendar_today_outlined, 'Period',
              '${grupo.dataInicio} → ${grupo.dataFim ?? '?'}'),
        if (grupo.orcamento != null)
          _infoRow(Icons.attach_money, 'Budget',
              'R\$ ${grupo.orcamento!.toStringAsFixed(2)}'),
        if (grupo.tipoViagem != null)
          _infoRow(Icons.category_outlined, 'Type', grupo.tipoViagem!),
        if (grupo.preferencias != null && grupo.preferencias!.isNotEmpty)
          _infoRow(Icons.favorite_outline, 'Preferences',
              grupo.preferencias!),
        const SizedBox(height: 20),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.surfaceVariant,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: AppTheme.primary.withValues(alpha: 0.2)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.auto_awesome,
                      color: AppTheme.primary, size: 18),
                  SizedBox(width: 8),
                  Text('AI Assistant Tips',
                      style: TextStyle(
                          fontWeight: FontWeight.w700, fontSize: 15)),
                ],
              ),
              const SizedBox(height: 12),
              const Text('Try asking the AI assistant:',
                  style: TextStyle(
                      color: AppTheme.onSurfaceMuted, fontSize: 12)),
              const SizedBox(height: 8),
              ..._aiTips.map((tip) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('💬',
                            style: TextStyle(fontSize: 13)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(tip,
                              style: const TextStyle(
                                  fontSize: 13,
                                  color: AppTheme.onSurface)),
                        ),
                      ],
                    ),
                  )),
            ],
          ),
        ),
        const SizedBox(height: 20),
        const Text('Invite Code',
            style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: () {
            Clipboard.setData(
                ClipboardData(text: grupo.codigoConvite ?? ''));
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Code copied!')),
            );
          },
          child: Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: AppTheme.surfaceVariant,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                  color: AppTheme.primary.withValues(alpha: 0.3)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  grupo.codigoConvite ?? '—',
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 4,
                  ),
                ),
                const Icon(Icons.copy,
                    color: AppTheme.primary, size: 20),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _infoRow(IconData icon, String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 18, color: AppTheme.onSurfaceMuted),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        color: AppTheme.onSurfaceMuted, fontSize: 12)),
                Text(value, style: const TextStyle(fontSize: 15)),
              ],
            ),
          ],
        ),
      );
}
