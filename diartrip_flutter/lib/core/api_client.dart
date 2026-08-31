import 'dart:async';

import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';
import 'package:flutter/foundation.dart';

import 'constants.dart';
import 'http_adapter_stub.dart' if (dart.library.html) 'http_adapter_web.dart';
import 'web_csrf_stub.dart' if (dart.library.html) 'web_csrf_web.dart';
import 'cookie_manager_stub.dart'
    if (dart.library.io) 'cookie_manager_native.dart'
    if (dart.library.html) 'cookie_manager_web.dart';

late final Dio dio;
late final CookieJar cookieJar;

const _csrfCookieNames = ['csrf_token', 'csrftoken'];

Future<void> initApiClient() async {
  cookieJar = await getPlatformCookieJar();

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
    _CsrfInterceptor(cookieJar),
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

class _RefreshInterceptor extends Interceptor {
  final CookieJar _jar;
  Completer<bool>? _refreshCompleter;

  _RefreshInterceptor(this._jar);

  @override
  Future<void> onResponse(
    Response response,
    ResponseInterceptorHandler handler,
  ) async {
    final path = response.requestOptions.path;
    if (response.statusCode != 401 ||
        path.contains('/token/refresh') ||
        path.contains('/login')) {
      handler.next(response);
      return;
    }

    if (_refreshCompleter != null) {
      final refreshed = await _refreshCompleter!.future;
      if (refreshed) {
        try {
          final opts = response.requestOptions;
          final newToken = await _readCsrfToken(opts.uri);
          if (newToken != null) {
            opts.headers['X-CSRF-Token'] = newToken;
            opts.headers['X-CSRFToken'] = newToken;
          }
          final retry = await dio.fetch(opts);
          handler.resolve(retry);
          return;
        } catch (_) {}
      }
      handler.next(response);
      return;
    }

    _refreshCompleter = Completer<bool>();
    try {
      final refreshed = await _tryRefresh();
      _refreshCompleter!.complete(refreshed);
      if (refreshed) {
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
      _refreshCompleter!.complete(false);
    } finally {
      _refreshCompleter = null;
    }
    handler.next(response);
  }

  Future<bool> _tryRefresh() async {
    try {
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

/// Erro de API que preserva o status HTTP além da mensagem já extraída por
/// [apiError]. `toString()` retorna só a mensagem — todo o código existente
/// que faz `catch (e) { _erro = e.toString(); }` continua funcionando sem
/// nenhuma mudança; só quem precisa decidir algo pelo status (ex.: 409 de
/// e-mail duplicado no cadastro) usa [statusCode].
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  const ApiException(this.message, [this.statusCode]);
  @override
  String toString() => message;
}

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
