import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme.dart';
import '../providers/auth_provider.dart';
import 'avatar_widget.dart';

class AppDrawer extends StatelessWidget {
  final String activeRoute;
  const AppDrawer({super.key, required this.activeRoute});

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthProvider>();
    final user = auth.usuario;

    return Drawer(
      backgroundColor: AppTheme.surface,
      child: SafeArea(
        child: Column(
          children: [
            // Cabeçalho do usuário
            Padding(
              padding: const EdgeInsets.all(20),
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
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user?.nome ?? '',
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 15,
                            color: AppTheme.onSurface,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          user?.email ?? '',
                          style: const TextStyle(
                            color: AppTheme.onSurfaceMuted,
                            fontSize: 12,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            const SizedBox(height: 8),
            // Itens de menu
            _item(context, Icons.home_outlined, 'My Trips', '/lobby'),
            _item(context, Icons.groups_outlined, 'Groups', '/grupos'),
            _item(context, Icons.dynamic_feed_outlined, 'Feed', '/feed'),
            _item(context, Icons.person_outline, 'Profile', '/perfil/${user?.id}'),
            _item(context, Icons.settings_outlined, 'Settings', '/config'),
            const Spacer(),
            const Divider(height: 1),
            // Logout
            ListTile(
              leading: const Icon(Icons.logout, color: AppTheme.error, size: 20),
              title: const Text(
                'Sign Out',
                style: TextStyle(color: AppTheme.error, fontSize: 14),
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

  Widget _item(BuildContext context, IconData icon, String label, String route) {
    final active = activeRoute == route || activeRoute.startsWith(route.split('?')[0]);
    return ListTile(
      leading: Icon(
        icon,
        color: active ? AppTheme.primary : AppTheme.onSurfaceMuted,
        size: 20,
      ),
      title: Text(
        label,
        style: TextStyle(
          color: active ? AppTheme.primary : AppTheme.onSurface,
          fontWeight: active ? FontWeight.w600 : FontWeight.normal,
          fontSize: 14,
        ),
      ),
      tileColor: active ? AppTheme.primary.withValues(alpha: 0.08) : null,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
      onTap: () {
        Navigator.pop(context);
        _go(context, route);
      },
    );
  }

  void _go(BuildContext context, String route) {
    if (activeRoute == route) return;
    Navigator.pushNamed(context, route);
  }
}
