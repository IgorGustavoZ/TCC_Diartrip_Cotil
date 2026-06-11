import 'package:flutter/foundation.dart';

class Constants {
  /// Quando servido pelo próprio FastAPI (/app), usa URL relativa (sem host).
  /// Android emulator  → http://10.0.2.2:8000
  /// iOS / Desktop     → http://127.0.0.1:8000
  static String get baseUrl {
    if (kIsWeb) {
      // Em produção o Flutter é servido pelo FastAPI (mesma origem → URL relativa).
      // Em dev (flutter run -d chrome) o servidor usa porta diferente de 8000, então
      // aponta para o backend usando o MESMO host (localhost) para que os cookies
      // SameSite=Strict funcionem — localhost:PORT e localhost:8000 são mesmo "site".
      final port = Uri.base.port;
      if (port != 0 && port != 80 && port != 443 && port != 8000) {
        return 'http://${Uri.base.host}:8000';
      }
      return '';
    }
    if (_isAndroid) return 'http://10.0.2.2:8000';
    return 'http://127.0.0.1:8000';
  }

  static String get wsBaseUrl {
    if (kIsWeb) {
      final port = Uri.base.port;
      if (port != 0 && port != 80 && port != 443 && port != 8000) {
        return 'ws://${Uri.base.host}:8000'; // mesmo host para SameSite funcionar
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
