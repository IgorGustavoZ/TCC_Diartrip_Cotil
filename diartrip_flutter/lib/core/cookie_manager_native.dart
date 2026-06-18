import 'dart:io';
import 'package:cookie_jar/cookie_jar.dart';
import 'package:path_provider/path_provider.dart';

Future<CookieJar> getPlatformCookieJar() async {
  final dir = await getApplicationDocumentsDirectory();
  final path = Directory('${dir.path}/.cookies/');
  if (!await path.exists()) {
    await path.create(recursive: true);
  }
  return PersistCookieJar(
    storage: FileStorage(path.path),
    ignoreExpires: false,
  );
}
