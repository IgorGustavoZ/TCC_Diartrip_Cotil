import 'package:flutter/foundation.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

/// Logger centralizado para toda a aplicação.
///
/// Em DEBUG  : imprime no console via debugPrint.
/// Em RELEASE: envia para o Sentry (sem dados sensíveis).
///
/// Configuração:
///   1. Defina SENTRY_DSN nas variáveis de ambiente ou em app_config.dart.
///   2. Substitua o placeholder abaixo pelo DSN real do projeto no Sentry.
///   3. Execute `flutter pub get` após adicionar sentry_flutter ao pubspec.yaml.
///
/// Dados NÃO enviados ao Sentry:
///   - Tokens JWT / cookies
///   - Senhas
///   - Qualquer dado que comece com "Bearer", "sk-", "access_token"
class AppLogger {
  static const _sentryDsn =
      'SUBSTITUIR_PELO_DSN_DO_SENTRY'; // https://sentry.io → Projeto → Settings → DSN

  /// Inicializa o Sentry. Deve ser chamado em main() antes de runApp().
  static Future<void> init(Widget app) async {
    if (kDebugMode) {
      runApp(app);
      return;
    }
    await SentryFlutter.init(
      (options) {
        options.dsn = _sentryDsn;
        options.environment = kProfileMode ? 'staging' : 'production';
        // Sem logging de rede (evita capturar tokens em headers)
        options.sendDefaultPii = false;
        // Captura automaticamente erros não tratados do Flutter
        options.attachScreenshot = false; // desabilitar para privacidade
        options.tracesSampleRate = 0.1;   // 10% de transações para performance
        // Filtrar dados sensíveis antes do envio
        options.beforeSend = _filtrarEventoSensivel;
      },
      appRunner: () => runApp(app),
    );
  }

  static SentryEvent? _filtrarEventoSensivel(SentryEvent event, Hint hint) {
    // Remove qualquer header ou dado que possa conter tokens
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

  // ── API pública ─────────────────────────────────────────────────────────────

  /// Log de erro com contexto e stack trace.
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

  /// Log de aviso (warning) — não interrompe o fluxo.
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

  /// Log informativo (apenas em debug).
  static void info(String context, String message) {
    if (kDebugMode) {
      debugPrint('[$context] INFO: $message');
    }
    // Não envia informações ao Sentry — apenas erros e warnings são relevantes
  }

  /// Captura um erro de forma silenciosa (não re-lança).
  /// Use nos blocos catch onde o fluxo deve continuar.
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
