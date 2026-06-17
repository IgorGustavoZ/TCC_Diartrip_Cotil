import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../../core/theme.dart';
import '../../../models/grupo.dart';
import '../../../providers/language_provider.dart';

class InfoTab extends StatelessWidget {
  final Grupo grupo;
  const InfoTab({super.key, required this.grupo});

  List<String> _aiTips(LanguageProvider lang) => [
    lang.translate('info.aiTip1'),
    lang.translate('info.aiTip2'),
    lang.translate('info.aiTip3'),
    lang.translate('info.aiTip4'),
    lang.translate('info.aiTip5'),
    lang.translate('info.aiTip6'),
  ];

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
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
        _infoRow(Icons.location_on_outlined, lang.translate('info.destination'),
            grupo.destinoPrincipal),
        if (grupo.dataInicio != null)
          _infoRow(Icons.calendar_today_outlined, lang.translate('info.period'),
              '${grupo.dataInicio} → ${grupo.dataFim ?? '?'}'),
        if (grupo.orcamento != null)
          _infoRow(Icons.attach_money, lang.translate('info.budget'),
              'R\$ ${grupo.orcamento!.toStringAsFixed(2)}'),
        if (grupo.tipoViagem != null)
          _infoRow(Icons.category_outlined, lang.translate('info.type'), grupo.tipoViagem!),
        if (grupo.preferencias != null && grupo.preferencias!.isNotEmpty)
          _infoRow(Icons.favorite_outline, lang.translate('info.preferences'),
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
              Row(
                children: [
                  const Icon(Icons.auto_awesome,
                      color: AppTheme.primary, size: 18),
                  const SizedBox(width: 8),
                  Text(lang.translate('info.aiTipsTitle'),
                      style: const TextStyle(
                          fontWeight: FontWeight.w700, fontSize: 15)),
                ],
              ),
              const SizedBox(height: 12),
              Text(lang.translate('info.aiTipsSubtitle'),
                  style: const TextStyle(
                      color: AppTheme.onSurfaceMuted, fontSize: 12)),
              const SizedBox(height: 8),
              ..._aiTips(lang).map((tip) => Padding(
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
        Text(lang.translate('info.inviteCode'),
            style: const TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: () {
            Clipboard.setData(
                ClipboardData(text: grupo.codigoConvite ?? ''));
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(lang.translate('info.codeCopied'))),
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
