import 'dart:ui';

import 'package:flutter/material.dart';

/// Design tokens copied 1:1 from `backend/frontend/static/style.css` (`:root`).
/// Shared by every screen that is being restyled to match the web app
/// (dashboard/app-shell pages), independently of [AppTheme] which still
/// drives the screens that haven't been visually audited yet.
class WebColors {
  WebColors._();

  static const bg = Color(0xFF0B1220);
  static const bg2 = Color(0xFF0F172A);
  static const surface = Color(0x0BFFFFFF); // rgba(255,255,255,.045)
  static const surface2 = Color(0x08FFFFFF); // rgba(255,255,255,.03)
  static const border = Color(0x17FFFFFF); // rgba(255,255,255,.09)
  static const borderStrong = Color(0x2EFFFFFF); // rgba(255,255,255,.18)
  static const text = Color(0xFFF1F5F9);
  static const textSecondary = Color(0xFFCBD5E1);
  static const textMuted = Color(0xFF94A3B8);
  static const primary = Color(0xFF2563EB);
  static const primaryHover = Color(0xFF1D4ED8);
  static const accent = Color(0xFF06B6D4);
  static const violet = Color(0xFF7C3AED);
  static const danger = Color(0xFFF87171);
  static const success = Color(0xFF4ADE80);
  static const warning = Color(0xFFD97706);

  static const radiusSm = 8.0;
  static const radiusMd = 12.0;
  static const radiusLg = 16.0;
  static const radiusPill = 999.0;

  static const gradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [primary, accent],
  );
}

/// Glassmorphism surface: `background: var(--surface); border: 1px solid
/// var(--border); backdrop-filter: blur(14px);` — no padding of its own,
/// matching how `.card`/`.trip-card`/`.dashboard-card` only set the
/// background treatment and let each usage decide inner spacing.
class GlassContainer extends StatelessWidget {
  final Widget child;
  final double radius;
  final Color? color;
  final Color? borderColor;
  final EdgeInsetsGeometry padding;

  const GlassContainer({
    super.key,
    required this.child,
    this.radius = WebColors.radiusLg,
    this.color,
    this.borderColor,
    this.padding = EdgeInsets.zero,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: color ?? WebColors.surface,
            borderRadius: BorderRadius.circular(radius),
            border: Border.all(color: borderColor ?? WebColors.border),
          ),
          child: child,
        ),
      ),
    );
  }
}

/// `.trip-card-expanded`: big glass card with an h2-style header — the main
/// content block repeated across every tab of viagem.html.
class TripCardExpanded extends StatelessWidget {
  final String title;
  final Widget child;
  final Color? titleColor;
  final Color? borderColor;
  final EdgeInsetsGeometry padding;

  const TripCardExpanded({
    super.key,
    required this.title,
    required this.child,
    this.titleColor,
    this.borderColor,
    this.padding = const EdgeInsets.all(20),
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: GlassContainer(
        borderColor: borderColor,
        padding: padding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: TextStyle(
                    color: titleColor ?? WebColors.text, fontWeight: FontWeight.w700, fontSize: 17)),
            const SizedBox(height: 16),
            child,
          ],
        ),
      ),
    );
  }
}

/// `.dashboard-card`: smaller card with an uppercase muted header — used
/// inside the dashboard grids (Overview/My Finances/Admin tabs). Always
/// nested inside an already-blurred [TripCardExpanded], so this one skips
/// its own `BackdropFilter` — blurring an already-opaque surface is wasted
/// GPU work and stacking many of these is a real source of jank on web.
class DashboardCard extends StatelessWidget {
  final String title;
  final Widget child;
  const DashboardCard({super.key, required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: WebColors.surface2,
        borderRadius: BorderRadius.circular(WebColors.radiusLg),
        border: Border.all(color: WebColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title.toUpperCase(),
            style: const TextStyle(
              color: WebColors.textMuted,
              fontWeight: FontWeight.w700,
              fontSize: 12,
              letterSpacing: 0.6,
            ),
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }
}

/// `.stat-row`: label/value pair, muted label + bold value.
class StatRow extends StatelessWidget {
  final String label;
  final String value;
  final Color? valueColor;
  const StatRow({super.key, required this.label, required this.value, this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: WebColors.textSecondary, fontSize: 14)),
          Text(value,
              style: TextStyle(
                  color: valueColor ?? WebColors.text, fontWeight: FontWeight.w700, fontSize: 18)),
        ],
      ),
    );
  }
}

/// `.category-item`: a bordered row inside a `.category-list`, e.g. a
/// spending category, a ranked member, or a recent expense.
class CategoryItemRow extends StatelessWidget {
  final Widget left;
  final Widget right;
  const CategoryItemRow({super.key, required this.left, required this.right});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: WebColors.border)),
      ),
      child: Row(
        children: [
          Expanded(child: left),
          const SizedBox(width: 8),
          right,
        ],
      ),
    );
  }
}

/// `.progress-container`/`.progress-bar`: gradient-filled budget bar.
class WebProgressBar extends StatelessWidget {
  final double value; // 0..1
  const WebProgressBar({super.key, required this.value});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(WebColors.radiusPill),
      child: Container(
        height: 10,
        color: WebColors.surface2,
        child: FractionallySizedBox(
          alignment: Alignment.centerLeft,
          widthFactor: value.clamp(0, 1),
          child: const DecoratedBox(decoration: BoxDecoration(gradient: WebColors.gradient)),
        ),
      ),
    );
  }
}

/// `.cta` / `.new-trip` button: gradient fill, pill or rounded shape, glow shadow.
class GradientButton extends StatelessWidget {
  final Widget child;
  final VoidCallback? onPressed;
  final EdgeInsetsGeometry padding;
  final double radius;

  const GradientButton({
    super.key,
    required this.child,
    required this.onPressed,
    this.padding = const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
    this.radius = WebColors.radiusMd,
  });

  @override
  Widget build(BuildContext context) {
    final enabled = onPressed != null;
    return Material(
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(radius),
      child: InkWell(
        borderRadius: BorderRadius.circular(radius),
        onTap: onPressed,
        child: Opacity(
          opacity: enabled ? 1 : 0.5,
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              gradient: WebColors.gradient,
              borderRadius: BorderRadius.circular(radius),
              boxShadow: enabled
                  ? [
                      BoxShadow(
                        color: WebColors.primary.withValues(alpha: 0.32),
                        blurRadius: 20,
                        offset: const Offset(0, 8),
                      ),
                    ]
                  : null,
            ),
            child: DefaultTextStyle.merge(
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14),
              child: IconTheme.merge(data: const IconThemeData(color: Colors.white, size: 16), child: child),
            ),
          ),
        ),
      ),
    );
  }
}

/// Fixed dark canvas with soft ambient glows, reproducing `body{}` in
/// style.css — shared across every app-shell page (not just marketing ones).
class AmbientBackground extends StatelessWidget {
  const AmbientBackground({super.key});

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: WebColors.bg,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          _glow(top: -140, left: -100, size: 480, color: WebColors.primary, alpha: .18),
          _glow(top: -40, right: -120, size: 420, color: WebColors.accent, alpha: .13),
          _glow(bottom: -160, left: -80, size: 440, color: WebColors.primary, alpha: .10),
        ],
      ),
    );
  }

  Widget _glow({
    double? top,
    double? bottom,
    double? left,
    double? right,
    required double size,
    required Color color,
    required double alpha,
  }) {
    return Positioned(
      top: top,
      bottom: bottom,
      left: left,
      right: right,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(colors: [color.withValues(alpha: alpha), Colors.transparent]),
        ),
      ),
    );
  }
}

/// Deterministic gradient cover per trip, mirroring `CAPAS`/`capaPara()` in
/// `backend/frontend/lobby.html` — same 6 gradients, same hash function
/// (so the same destination gets the same cover color as on the web).
const List<List<Color>> tripCoverGradients = [
  [Color(0xFF2563EB), Color(0xFF06B6D4)],
  [Color(0xFF7C3AED), Color(0xFFC026D3)],
  [Color(0xFF0891B2), Color(0xFF16A34A)],
  [Color(0xFFEA580C), Color(0xFFF59E0B)],
  [Color(0xFFDB2777), Color(0xFFF43F5E)],
  [Color(0xFF0D9488), Color(0xFF2563EB)],
];

LinearGradient tripCoverGradientFor(String texto) {
  var hash = 0;
  for (final unit in texto.codeUnits) {
    hash = (hash * 31 + unit) & 0xFFFFFFFF;
  }
  final colors = tripCoverGradients[hash % tripCoverGradients.length];
  return LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: colors,
  );
}
