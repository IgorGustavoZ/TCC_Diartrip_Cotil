import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/web_style.dart';
import '../providers/auth_provider.dart';
import '../providers/language_provider.dart';
import 'avatar_widget.dart';

/// Sidebar navigation, mirroring `.sidebar`/`.menu-item`/`.new-trip` in
/// backend/frontend/style.css: dark glass background, primary-tinted active
/// state, gradient "New Trip" button, red logout. Every item uses an emoji
/// (matching the site's own `.menu-item` glyphs) rather than a Material
/// icon — Explorar Viagens gets 🧭 instead of reusing ✈️ like the web does,
/// since a repeated plane emoji right under "Minhas Viagens" was already
/// flagged as confusing earlier.
class AppDrawer extends StatelessWidget {
  final String activeRoute;
  const AppDrawer({super.key, required this.activeRoute});

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthProvider>();
    final user = auth.usuario;
    final lang = context.watch<LanguageProvider>();

    return Drawer(
      backgroundColor: WebColors.bg,
      child: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
              child: Row(
                children: [
                  AvatarWidget(
                    fotoUrl: user?.fotoPerfil,
                    iniciais: user?.iniciais ?? '?',
                    radius: 22,
                    onTap: () => _go(context, '/perfil/${user?.id}'),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      user?.nome ?? '',
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 15,
                        color: WebColors.text,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
            Divider(height: 1, color: WebColors.border),
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              child: Column(
                children: [
                  _item(context, '✈️', lang.translate('nav.myTrips'), '/lobby'),
                  _item(context, '🌐', lang.translate('nav.groups'), '/grupos'),
                  _item(context, '🧭', lang.translate('nav.explore'), '/explorar'),
                  _item(context, '📰', lang.translate('nav.feed'), '/feed'),
                  _item(context, '⚙️', lang.translate('nav.settings'), '/config'),
                  const SizedBox(height: 8),
                  GradientButton(
                    onPressed: () {
                      Navigator.pop(context);
                      Navigator.pushNamed(context, '/nova-viagem');
                    },
                    padding: const EdgeInsets.symmetric(vertical: 13),
                    child: SizedBox(
                      width: double.infinity,
                      child: Text('+ ${lang.translate('lobby.newTrip')}', textAlign: TextAlign.center),
                    ),
                  ),
                ],
              ),
            ),
            const Spacer(),
            Divider(height: 1, color: WebColors.border),
            ListTile(
              leading: const Icon(Icons.logout, color: WebColors.danger, size: 20),
              title: Text(
                lang.translate('nav.signOut'),
                style: const TextStyle(color: WebColors.danger, fontSize: 14, fontWeight: FontWeight.w600),
              ),
              onTap: () async {
                Navigator.pop(context);
                await auth.logout();
                if (context.mounted) {
                  Navigator.pushNamedAndRemoveUntil(context, '/login', (_) => false);
                }
              },
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  Widget _item(BuildContext context, String emoji, String label, String route) {
    final active = _isActive(route);
    return _navRow(
      context,
      Text(emoji, style: const TextStyle(fontSize: 17)),
      label,
      route,
      active,
    );
  }

  bool _isActive(String route) => activeRoute == route || activeRoute.startsWith(route.split('?')[0]);

  Widget _navRow(BuildContext context, Widget leading, String label, String route, bool active) {
    return Material(
      color: active ? WebColors.primary.withValues(alpha: 0.14) : Colors.transparent,
      borderRadius: BorderRadius.circular(WebColors.radiusMd),
      child: InkWell(
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
        onTap: () {
          Navigator.pop(context);
          _go(context, route);
        },
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            children: [
              SizedBox(width: 20, child: Center(child: leading)),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    color: active ? WebColors.primary : WebColors.textSecondary,
                    fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                    fontSize: 14,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _go(BuildContext context, String route) {
    if (activeRoute == route) return;
    Navigator.pushNamed(context, route);
  }
}
