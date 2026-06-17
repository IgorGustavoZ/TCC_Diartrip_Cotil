// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

/// Lê o token CSRF de document.cookie no Flutter Web.
///
/// Cobre os nomes padrão de FastAPI ("csrf_token") e Django ("csrftoken").
/// O cookie NÃO pode ter o atributo HttpOnly — caso contrário o browser
/// bloqueia a leitura e este método retorna null.
String? readWebCsrfToken() {
  const names = ['csrf_token', 'csrftoken'];
  try {
    final raw = html.document.cookie ?? '';
    final map = <String, String>{};
    for (final part in raw.split(';')) {
      final t = part.trim();
      final eq = t.indexOf('=');
      if (eq > 0) {
        map[t.substring(0, eq).trim()] =
            Uri.decodeComponent(t.substring(eq + 1).trim());
      }
    }
    for (final name in names) {
      final v = map[name];
      if (v != null && v.isNotEmpty) return v;
    }
  } catch (_) {}
  return null;
}
