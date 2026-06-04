import 'package:flutter_test/flutter_test.dart';
import 'package:diartrip_flutter/models/grupo.dart';

void main() {
  group('Grupo.fromJson', () {
    test('campos obrigatórios mapeados', () {
      final g = Grupo.fromJson({
        'id_grupo': 10,
        'nome_grupo': 'Paris 2026',
        'destino_principal': 'Paris',
      });
      expect(g.id, 10);
      expect(g.nomeGrupo, 'Paris 2026');
      expect(g.destinoPrincipal, 'Paris');
    });

    test('campos opcionais nulos quando ausentes', () {
      final g = Grupo.fromJson({
        'id_grupo': 1,
        'nome_grupo': 'G',
        'destino_principal': 'D',
      });
      expect(g.dataInicio, isNull);
      expect(g.dataFim, isNull);
      expect(g.orcamento, isNull);
      expect(g.tipoViagem, isNull);
      expect(g.preferencias, isNull);
      expect(g.codigoConvite, isNull);
      expect(g.criadorId, isNull);
    });

    test('orçamento como int é convertido para double', () {
      final g = Grupo.fromJson({
        'id_grupo': 1,
        'nome_grupo': 'G',
        'destino_principal': 'D',
        'orcamento': 5000,
      });
      expect(g.orcamento, isA<double>());
      expect(g.orcamento, 5000.0);
    });

    test('todos os campos preenchidos', () {
      final g = Grupo.fromJson({
        'id_grupo': 7,
        'nome_grupo': 'Aventura no Japão',
        'destino_principal': 'Tóquio',
        'data_inicio': '2026-07-01',
        'data_fim': '2026-07-15',
        'orcamento': 12000.50,
        'tipo_viagem': 'Cultural',
        'preferencias': 'museus, gastronomia',
        'codigo_convite': 'ABC123',
        'criador_id': 99,
      });
      expect(g.dataInicio, '2026-07-01');
      expect(g.dataFim, '2026-07-15');
      expect(g.orcamento, 12000.50);
      expect(g.tipoViagem, 'Cultural');
      expect(g.preferencias, 'museus, gastronomia');
      expect(g.codigoConvite, 'ABC123');
      expect(g.criadorId, 99);
    });
  });

  group('Membro.fromJson', () {
    test('membro com cargo admin', () {
      final m = Membro.fromJson({
        'id_usuario': 1,
        'nome': 'Admin User',
        'foto_perfil': null,
        'cargo': 'admin',
      });
      expect(m.id, 1);
      expect(m.nome, 'Admin User');
      expect(m.cargo, 'admin');
      expect(m.isAdmin, isTrue);
      expect(m.fotoPerfil, isNull);
    });

    test('membro com cargo comum não é admin', () {
      final m = Membro.fromJson({
        'id_usuario': 2,
        'nome': 'Normal User',
        'foto_perfil': 'https://cdn.test/foto.jpg',
        'cargo': 'membro',
      });
      expect(m.isAdmin, isFalse);
      expect(m.fotoPerfil, 'https://cdn.test/foto.jpg');
    });
  });
}
