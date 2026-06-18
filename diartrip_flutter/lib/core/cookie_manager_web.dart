import 'package:cookie_jar/cookie_jar.dart';

Future<CookieJar> getPlatformCookieJar() async {
  return DefaultCookieJar();
}
