import 'package:flutter_test/flutter_test.dart';
import 'package:diartrip_flutter/models/roteiro.dart';

void main() {
  group('Roteiro.fromJson', () {
    test('todos os campos mapeados', () {
      final r = Roteiro.fromJson({
        'id_roteiro': 1,
        'id_grupo': 10,
        'titulo': 'Dia 1 — Torre Eiffel',
        'descricao': 'Visitar às 9h, almoço no Champs-Élysées',
      });
      expect(r.id, 1);
      expect(r.idGrupo, 10);
      expect(r.titulo, 'Dia 1 — Torre Eiffel');
      expect(r.descricao, 'Visitar às 9h, almoço no Champs-Élysées');
    });

    test('descrição ausente assume string vazia', () {
      final r = Roteiro.fromJson({
        'id_roteiro': 2,
        'id_grupo': 5,
        'titulo': 'Dia livre',
      });
      expect(r.descricao, '');
    });

    test('descrição nula assume string vazia', () {
      final r = Roteiro.fromJson({
        'id_roteiro': 3,
        'id_grupo': 5,
        'titulo': 'Dia livre',
        'descricao': null,
      });
      expect(r.descricao, '');
    });

    test('IDs diferentes mapeados corretamente', () {
      final r = Roteiro.fromJson({
        'id_roteiro': 99,
        'id_grupo': 42,
        'titulo': 'Check-out',
        'descricao': 'Devolver quarto até 12h',
      });
      expect(r.id, 99);
      expect(r.idGrupo, 42);
    });
  });
}
