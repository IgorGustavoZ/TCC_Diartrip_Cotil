import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

import 'constants.dart';
import 'http_adapter_stub.dart' if (dart.library.html) 'http_adapter_web.dart';
import 'web_csrf_stub.dart' if (dart.library.html) 'web_csrf_web.dart';

late final Dio dio;
late final CookieJar cookieJar;

const _csrfCookieNames = ['csrf_token', 'csrftoken'];

Future<void> initApiClient() async {
  if (kIsWeb) {
    cookieJar = DefaultCookieJar();
  } else {
    final dir = await getApplicationDocumentsDirectory();
    cookieJar = PersistCookieJar(
      storage: FileStorage('${dir.path}/.cookies/'),
      ignoreExpires: false,
    );
  }

  dio = Dio(BaseOptions(
    baseUrl: Constants.baseUrl,
    connectTimeout: Constants.connectTimeout,
    receiveTimeout: Constants.receiveTimeout,
    contentType: Headers.jsonContentType,
    headers: const {'Accept': 'application/json'},
    validateStatus: (status) => status != null && status < 500,
  ));

  applyWebCredentials(dio);

  dio.interceptors.addAll([
    if (!kIsWeb) CookieManager(cookieJar),

    // Injeta X-CSRF-Token em mutações
    _CsrfInterceptor(cookieJar),

    // Renova access token automaticamente quando recebe 401
    _RefreshInterceptor(cookieJar),

    if (kDebugMode)
      LogInterceptor(
        requestHeader: false,
        requestBody: true,
        responseHeader: false,
        responseBody: true,
        error: true,
        logPrint: (o) => debugPrint('[Dio] $o'),
      ),
  ]);
}

// ─── Interceptor de CSRF ──────────────────────────────────────────────────────

class _CsrfInterceptor extends Interceptor {
  final CookieJar _jar;
  static const _mutating = {'POST', 'PUT', 'PATCH', 'DELETE'};

  _CsrfInterceptor(this._jar);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (!_mutating.contains(options.method.toUpperCase())) {
      return handler.next(options);
    }
    final token = await _readToken(options.uri);
    if (token != null && token.isNotEmpty) {
      options.headers['X-CSRF-Token'] = token;
      options.headers['X-CSRFToken'] = token;
    }
    handler.next(options);
  }

  Future<String?> _readToken(Uri uri) async {
    try {
      if (kIsWeb) return readWebCsrfToken();
      final cookies = await _jar.loadForRequest(uri);
      for (final name in _csrfCookieNames) {
        final match = cookies.where((c) => c.name == name).firstOrNull;
        if (match != null && match.value.isNotEmpty) return match.value;
      }
    } catch (_) {}
    return null;
  }
}

// ─── Interceptor de Refresh Token ─────────────────────────────────────────────

class _RefreshInterceptor extends Interceptor {
  final CookieJar _jar;
  bool _refreshing = false;

  _RefreshInterceptor(this._jar);

  @override
  Future<void> onResponse(
    Response response,
    ResponseInterceptorHandler handler,
  ) async {
    // Ignora o próprio endpoint de refresh para evitar loop infinito
    final path = response.requestOptions.path;
    if (response.statusCode == 401 &&
        !path.contains('/token/refresh') &&
        !path.contains('/login')) {
      if (_refreshing) {
        handler.next(response);
        return;
      }
      _refreshing = true;
      try {
        final refreshed = await _tryRefresh();
        if (refreshed) {
          // Refaz a requisição original com os novos cookies
          final opts = response.requestOptions;
          final newToken = await _readCsrfToken(opts.uri);
          if (newToken != null) {
            opts.headers['X-CSRF-Token'] = newToken;
            opts.headers['X-CSRFToken'] = newToken;
          }
          final retry = await dio.fetch(opts);
          handler.resolve(retry);
          return;
        }
      } catch (_) {
        // Refresh falhou — deixa o 401 propagar normalmente
      } finally {
        _refreshing = false;
      }
    }
    handler.next(response);
  }

  Future<bool> _tryRefresh() async {
    try {
      // POST /token/refresh — o browser/cookie jar envia refresh_token automaticamente
      final r = await dio.post('/token/refresh');
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<String?> _readCsrfToken(Uri uri) async {
    try {
      if (kIsWeb) return readWebCsrfToken();
      final cookies = await _jar.loadForRequest(uri);
      for (final name in _csrfCookieNames) {
        final match = cookies.where((c) => c.name == name).firstOrNull;
        if (match != null && match.value.isNotEmpty) return match.value;
      }
    } catch (_) {}
    return null;
  }
}

// ─── Utilitários públicos ─────────────────────────────────────────────────────

/// Extrai mensagem legível de respostas de erro da API.
String apiError(dynamic data, [String fallback = 'Erro desconhecido']) {
  if (data is! Map) return fallback;
  final detail = data['detail'];
  if (detail == null) {
    return (data['message'] as String?)?.trim().isNotEmpty == true
        ? data['message'] as String
        : fallback;
  }
  if (detail is String) return detail.isEmpty ? fallback : detail;
  if (detail is List && detail.isNotEmpty) {
    final first = detail.first;
    if (first is Map) {
      final msg = (first['msg'] as String?) ?? first.toString();
      return msg.startsWith('Value error, ') ? msg.substring(13) : msg;
    }
    return first.toString();
  }
  return fallback;
}

/// Constrói o header `Cookie: …` a partir do jar nativo (usado no WebSocket).
Future<String> buildCookieHeader() async {
  if (kIsWeb) return '';
  try {
    final uri = Uri.parse(Constants.baseUrl);
    final cookies = await cookieJar.loadForRequest(uri);
    return cookies.map((c) => '${c.name}=${c.value}').join('; ');
  } catch (_) {
    return '';
  }
}

/// Retorna o token CSRF do jar (I/O) ou de document.cookie (Web).
Future<String?> getCsrfToken() async {
  try {
    if (kIsWeb) return readWebCsrfToken();
    final uri = Uri.parse(Constants.baseUrl);
    final cookies = await cookieJar.loadForRequest(uri);
    for (final name in _csrfCookieNames) {
      final match = cookies.where((c) => c.name == name).firstOrNull;
      if (match != null && match.value.isNotEmpty) return match.value;
    }
  } catch (_) {}
  return null;
}
