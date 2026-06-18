import 'package:flutter/foundation.dart';

const String _kApiBaseUrl = String.fromEnvironment('API_BASE_URL');
const String _kApiWsUrl  = String.fromEnvironment('API_WS_URL');

class Constants {
  static String get baseUrl {
    if (_kApiBaseUrl.isNotEmpty) return _kApiBaseUrl;

    if (kIsWeb) {
      final port = Uri.base.port;
      if (port == 8000) return '';
      return 'http://${Uri.base.host}:8000';
    }
    if (_isAndroid) return 'http://10.0.2.2:8000';
    return 'http://127.0.0.1:8000';
  }

  static String get wsBaseUrl {
    if (_kApiWsUrl.isNotEmpty) return _kApiWsUrl;

    if (kIsWeb) {
      final port = Uri.base.port;
      if (port != 0 && port != 80 && port != 443 && port != 8000) {
        return 'ws://${Uri.base.host}:8000';
      }
      final proto = Uri.base.scheme == 'https' ? 'wss' : 'ws';
      return '$proto://${Uri.base.host}:${Uri.base.port}';
    }
    if (_isAndroid) return 'ws://10.0.2.2:8000';
    return 'ws://127.0.0.1:8000';
  }

  static bool get _isAndroid =>
      defaultTargetPlatform == TargetPlatform.android;

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 15);

  static const List<String> categorias = [
    'Transporte',
    'Alimentação',
    'Hospedagem',
    'Lazer',
    'Compras',
    'Saúde',
    'Outro',
  ];

  static const Map<String, String> categoriaEmoji = {
    'Transporte': '🚗',
    'Alimentação': '🍽️',
    'Hospedagem': '🏨',
    'Lazer': '🎭',
    'Compras': '🛍️',
    'Saúde': '💊',
    'Outro': '📦',
  };

  static const List<String> tiposViagem = [
    'Lazer',
    'Aventura',
    'Cultural',
    'Gastronômico',
    'Relaxamento',
    'Negócios',
  ];
}
