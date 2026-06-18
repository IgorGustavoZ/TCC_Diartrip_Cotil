import 'package:cookie_jar/cookie_jar.dart';

abstract class CookieManagerFactory {
  Future<CookieJar> createCookieJar();
}

Future<CookieJar> getPlatformCookieJar() => throw UnsupportedError('Cannot create cookie jar');
