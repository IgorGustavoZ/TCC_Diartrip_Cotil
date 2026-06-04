import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/api_client.dart';
import 'core/app_logger.dart';
import 'core/theme.dart';
import 'providers/auth_provider.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/register_screen.dart';
import 'screens/grupo/form_viagem_screen.dart';
import 'screens/grupo/grupos_screen.dart';
import 'screens/grupo/viagem_screen.dart';
import 'screens/home/lobby_screen.dart';
import 'screens/profile/config_screen.dart';
import 'screens/profile/perfil_screen.dart';
import 'screens/social/feed_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await initApiClient();
  } catch (e, s) {
    AppLogger.captureError('main.initApiClient', e, s, fatal: true);
  }

  // Captura erros Flutter do framework (ex: build errors em widgets)
  FlutterError.onError = (details) {
    AppLogger.captureError(
      'FlutterError',
      details.exception,
      details.stack,
      fatal: details.silent == false,
    );
  };

  final app = ChangeNotifierProvider(
    create: (_) => AuthProvider(),
    child: const DiartripApp(),
  );

  // AppLogger.init inicializa Sentry em release e chama runApp
  await AppLogger.init(app);
}

class DiartripApp extends StatelessWidget {
  const DiartripApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Diartrip',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      home: const _Splash(),
      onGenerateRoute: _generateRoute,
    );
  }

  Route<dynamic>? _generateRoute(RouteSettings s) {
    final name = s.name ?? '/';
    final uri = Uri.parse(name);
    final path = uri.path;

    if (path == '/login') return _page(const LoginScreen(), s);
    if (path == '/register') return _page(const RegisterScreen(), s);
    if (path == '/lobby') return _page(const LobbyScreen(), s);
    if (path == '/grupos') return _page(const GruposScreen(), s);
    if (path == '/feed') return _page(const FeedScreen(), s);
    if (path == '/nova-viagem') return _page(const FormViagemScreen(), s);
    if (path == '/config') return _page(const ConfigScreen(), s);

    final viagemMatch = RegExp(r'^/viagem/(\d+)$').firstMatch(path);
    if (viagemMatch != null) {
      final id = int.parse(viagemMatch.group(1)!);
      return _page(ViagemScreen(idGrupo: id), s);
    }

    final perfilMatch = RegExp(r'^/perfil/(\d+)$').firstMatch(path);
    if (perfilMatch != null) {
      final id = int.parse(perfilMatch.group(1)!);
      return _page(PerfilScreen(idUsuario: id), s);
    }

    if (path == '/perfil') return _page(const PerfilScreen(), s);

    return _page(const LobbyScreen(), s);
  }

  PageRoute<T> _page<T>(Widget w, RouteSettings s) =>
      MaterialPageRoute(builder: (_) => w, settings: s);
}

/// Verifica sessão salva e redireciona para Login ou Lobby.
class _Splash extends StatefulWidget {
  const _Splash();
  @override
  State<_Splash> createState() => _SplashState();
}

class _SplashState extends State<_Splash> {
  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    await context.read<AuthProvider>().tryAutoLogin();
    if (!mounted) return;
    final dest = context.read<AuthProvider>().isLoggedIn ? '/lobby' : '/login';
    Navigator.pushReplacementNamed(context, dest);
  }

  @override
  Widget build(BuildContext context) => const Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.flight_takeoff, size: 64, color: AppTheme.primary),
              SizedBox(height: 12),
              Text('Diartrip',
                  style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.onSurface)),
              SizedBox(height: 24),
              CircularProgressIndicator(),
            ],
          ),
        ),
      );
}
