import 'package:cookie_jar/cookie_jar.dart';

/// Define a interface para criação do CookieJar por plataforma.
abstract class CookieManagerFactory {
  Future<CookieJar> createCookieJar();
}

/// Stub que redireciona para a implementação correta via conditional imports.
Future<CookieJar> getPlatformCookieJar() => throw UnsupportedError('Cannot create cookie jar');
