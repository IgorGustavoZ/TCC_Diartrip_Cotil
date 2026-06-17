import 'package:flutter_test/flutter_test.dart';
import 'package:diartrip_flutter/models/usuario.dart';

void main() {
  group('Usuario.fromJson', () {
    test('campos obrigatórios mapeados corretamente', () {
      final u = Usuario.fromJson({
        'id_usuario': 42,
        'nome': 'Ana Lima',
        'email': 'ana@example.com',
      });
      expect(u.id, 42);
      expect(u.nome, 'Ana Lima');
      expect(u.email, 'ana@example.com');
    });

    test('email ausente em perfil público não causa crash', () {
      // Endpoint GET /usuarios/{id} não retorna email — não deve crashar
      final u = Usuario.fromJson({
        'id_usuario': 7,
        'nome': 'Carlos',
        'bio': 'Viajante',
        'foto_perfil': null,
        'data_criacao': '2026-01-01T00:00:00',
      });
      expect(u.id, 7);
      expect(u.nome, 'Carlos');
      expect(u.email, isNull);
    });

    test('email explicitamente nulo em perfil público não causa crash', () {
      final u = Usuario.fromJson({
        'id_usuario': 8,
        'nome': 'Diana',
        'email': null,
      });
      expect(u.email, isNull);
    });

    test('campos opcionais nulos quando ausentes', () {
      final u = Usuario.fromJson({
        'id_usuario': 1,
        'nome': 'João',
        'email': 'joao@x.com',
      });
      expect(u.bio, isNull);
      expect(u.fotoPerfil, isNull);
      expect(u.dataCriacao, isNull);
    });

    test('campos opcionais preenchidos', () {
      final u = Usuario.fromJson({
        'id_usuario': 5,
        'nome': 'Maria',
        'email': 'maria@x.com',
        'bio': 'Viajante',
        'foto_perfil': 'https://cdn.test/foto.jpg',
        'data_criacao': '2026-01-15T10:30:00',
      });
      expect(u.bio, 'Viajante');
      expect(u.fotoPerfil, 'https://cdn.test/foto.jpg');
      expect(u.dataCriacao, '2026-01-15T10:30:00');
    });
  });

  group('Usuario.iniciais', () {
    test('dois nomes retorna iniciais em maiúsculo', () {
      final u = Usuario.fromJson({'id_usuario': 1, 'nome': 'Pedro Costa', 'email': 'p@x.com'});
      expect(u.iniciais, 'PC');
    });

    test('nome único retorna primeira letra em maiúsculo', () {
      final u = Usuario.fromJson({'id_usuario': 1, 'nome': 'beatriz', 'email': 'b@x.com'});
      expect(u.iniciais, 'B');
    });

    test('nome vazio retorna ponto de interrogação', () {
      final u = Usuario.fromJson({'id_usuario': 1, 'nome': '', 'email': 'x@x.com'});
      expect(u.iniciais, '?');
    });

    test('três nomes usa apenas o primeiro e o segundo', () {
      final u = Usuario.fromJson({'id_usuario': 1, 'nome': 'Carlos Eduardo Silva', 'email': 'c@x.com'});
      expect(u.iniciais, 'CE');
    });

    test('nome com espaços extras usa partes não vazias', () {
      final u = Usuario.fromJson({'id_usuario': 1, 'nome': 'Ana', 'email': 'a@x.com'});
      expect(u.iniciais, 'A');
    });
  });
}
