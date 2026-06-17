import 'package:flutter_test/flutter_test.dart';
import 'package:diartrip_flutter/models/gasto.dart';

void main() {
  group('Gasto.fromJson', () {
    test('campos obrigatórios mapeados', () {
      final g = Gasto.fromJson({
        'id_gasto': 1,
        'id_grupo': 10,
        'id_usuario': 5,
        'nome': 'Ana',
        'valor': 150.0,
        'categoria': 'Alimentação',
      });
      expect(g.id, 1);
      expect(g.idGrupo, 10);
      expect(g.idUsuario, 5);
      expect(g.nomeUsuario, 'Ana');
      expect(g.valor, 150.0);
      expect(g.categoria, 'Alimentação');
    });

    test('valor inteiro convertido para double', () {
      final g = Gasto.fromJson({
        'id_gasto': 2,
        'id_usuario': 1,
        'valor': 200,
        'categoria': 'Transporte',
      });
      expect(g.valor, isA<double>());
      expect(g.valor, 200.0);
    });

    test('id_grupo ausente assume zero', () {
      final g = Gasto.fromJson({
        'id_gasto': 3,
        'id_usuario': 1,
        'valor': 50.0,
        'categoria': 'Lazer',
      });
      expect(g.idGrupo, 0);
    });

    test('nome ausente assume string vazia', () {
      final g = Gasto.fromJson({
        'id_gasto': 4,
        'id_usuario': 1,
        'valor': 30.0,
        'categoria': 'Outro',
      });
      expect(g.nomeUsuario, '');
    });

    test('lista de divisão mapeada', () {
      final g = Gasto.fromJson({
        'id_gasto': 5,
        'id_usuario': 1,
        'valor': 300.0,
        'categoria': 'Hospedagem',
        'id_usuarios_divisao': [1, 2, 3],
      });
      expect(g.idUsuariosDivisao, [1, 2, 3]);
    });

    test('divisão ausente assume lista vazia', () {
      final g = Gasto.fromJson({
        'id_gasto': 6,
        'id_usuario': 1,
        'valor': 10.0,
        'categoria': 'Saúde',
      });
      expect(g.idUsuariosDivisao, isEmpty);
    });

    test('campos opcionais presentes', () {
      final g = Gasto.fromJson({
        'id_gasto': 7,
        'id_usuario': 1,
        'valor': 75.0,
        'categoria': 'Compras',
        'descricao': 'Souvenirs',
        'data_gasto': '2026-06-10',
      });
      expect(g.descricao, 'Souvenirs');
      expect(g.dataGasto, '2026-06-10');
    });
  });
}
