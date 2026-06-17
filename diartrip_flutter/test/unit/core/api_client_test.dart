import 'package:flutter_test/flutter_test.dart';
import 'package:diartrip_flutter/core/api_client.dart';

void main() {
  group('apiError', () {
    test('retorna fallback quando data não é Map', () {
      expect(apiError('mensagem string', 'fallback'), 'fallback');
      expect(apiError(null, 'fb'), 'fb');
      expect(apiError(42, 'fb'), 'fb');
      expect(apiError(['a'], 'fb'), 'fb');
    });

    test('retorna fallback padrão sem argumento explícito', () {
      expect(apiError(null), 'Erro desconhecido');
    });

    test('detail como string retorna a string', () {
      expect(apiError({'detail': 'Email já cadastrado'}, 'fb'), 'Email já cadastrado');
    });

    test('detail string vazia retorna fallback', () {
      expect(apiError({'detail': ''}, 'fallback'), 'fallback');
    });

    test('detail como lista usa mensagem do primeiro item', () {
      final data = {
        'detail': [
          {'msg': 'Campo obrigatório', 'loc': ['body', 'nome']}
        ]
      };
      expect(apiError(data, 'fb'), 'Campo obrigatório');
    });

    test('detail lista com prefixo "Value error, " é removido', () {
      final data = {
        'detail': [
          {'msg': 'Value error, Senha muito curta'}
        ]
      };
      expect(apiError(data, 'fb'), 'Senha muito curta');
    });

    test('detail lista vazia retorna fallback', () {
      expect(apiError({'detail': []}, 'fallback'), 'fallback');
    });

    test('sem campo detail usa message quando presente', () {
      expect(apiError({'message': 'Acesso negado'}, 'fb'), 'Acesso negado');
    });

    test('sem detail nem message retorna fallback', () {
      expect(apiError({'code': 404}, 'fb'), 'fb');
    });

    test('message vazia retorna fallback', () {
      expect(apiError({'message': '  '}, 'fallback'), 'fallback');
    });

    test('detail com item não-Map usa toString', () {
      final data = {'detail': ['erro de validação']};
      expect(apiError(data, 'fb'), 'erro de validação');
    });
  });
}
