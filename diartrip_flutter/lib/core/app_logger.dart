import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

class AppLogger {
  static const _sentryDsn =
      'SUBSTITUIR_PELO_DSN_DO_SENTRY';

  static bool get _sentryConfigured =>
      _sentryDsn.isNotEmpty && !_sentryDsn.startsWith('SUBSTITUIR');

  static Future<void> init(Widget app) async {
    if (kDebugMode || !_sentryConfigured) {
      runApp(app);
      return;
    }
    await SentryFlutter.init(
      (options) {
        options.dsn = _sentryDsn;
        options.environment = kProfileMode ? 'staging' : 'production';
        options.sendDefaultPii = false;
        options.attachScreenshot = false;
        options.tracesSampleRate = 0.1;
        options.beforeSend = _filtrarEventoSensivel;
      },
      appRunner: () => runApp(app),
    );
  }

  static SentryEvent? _filtrarEventoSensivel(SentryEvent event, Hint hint) {
    final filtered = event.toJson();
    _redactSensitiveValues(filtered);
    return SentryEvent.fromJson(filtered);
  }

  static void _redactSensitiveValues(dynamic obj) {
    if (obj is Map) {
      for (final key in obj.keys) {
        final k = key.toString().toLowerCase();
        if (_isSensitiveKey(k)) {
          obj[key] = '[REDACTED]';
        } else {
          _redactSensitiveValues(obj[key]);
        }
      }
    } else if (obj is List) {
      for (final item in obj) {
        _redactSensitiveValues(item);
      }
    }
  }

  static bool _isSensitiveKey(String key) {
    const sensitive = {
      'authorization', 'token', 'password', 'senha', 'secret',
      'access_token', 'refresh_token', 'csrf_token', 'cookie',
      'set-cookie', 'api_key', 'apikey',
    };
    return sensitive.any((s) => key.contains(s));
  }

  static void error(
    String context,
    dynamic error, [
    StackTrace? stack,
  ]) {
    if (kDebugMode) {
      debugPrint('[$context] ERROR: $error');
      if (stack != null) debugPrint(stack.toString());
      return;
    }
    Sentry.captureException(
      error,
      stackTrace: stack,
      withScope: (scope) => scope.setTag('context', context),
    );
  }

  static void warning(String context, String message) {
    if (kDebugMode) {
      debugPrint('[$context] WARNING: $message');
      return;
    }
    Sentry.captureMessage(
      message,
      level: SentryLevel.warning,
      withScope: (scope) => scope.setTag('context', context),
    );
  }

  static void info(String context, String message) {
    if (kDebugMode) {
      debugPrint('[$context] INFO: $message');
    }
  }

  static void captureError(
    String context,
    dynamic error,
    StackTrace? stack, {
    bool fatal = false,
  }) {
    if (kDebugMode) {
      debugPrint('[$context] ${fatal ? "FATAL" : "ERROR"}: $error');
      if (stack != null) debugPrint(stack.toString());
      return;
    }
    Sentry.captureException(
      error,
      stackTrace: stack,
      withScope: (scope) {
        scope.setTag('context', context);
        scope.setTag('fatal', fatal.toString());
      },
    );
  }
}
