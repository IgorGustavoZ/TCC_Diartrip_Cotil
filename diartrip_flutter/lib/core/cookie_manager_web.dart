import 'package:cookie_jar/cookie_jar.dart';

/// Implementação para Web: usa o jar em memória (DefaultCookieJar).
/// Na Web, o navegador gerencia a persistência dos cookies nativamente.
Future<CookieJar> getPlatformCookieJar() async {
  return DefaultCookieJar();
}
