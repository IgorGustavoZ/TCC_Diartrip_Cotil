import 'package:flutter_test/flutter_test.dart';
import 'package:diartrip_flutter/models/post.dart';

void main() {
  group('Post.fromJson', () {
    test('campos obrigatórios mapeados', () {
      final p = Post.fromJson({
        'id_post': 1,
        'id_usuario': 5,
        'nome': 'Carlos',
        'conteudo': 'Viagem incrível!',
        'data_criacao': '2026-06-01T10:00:00',
      });
      expect(p.id, 1);
      expect(p.idUsuario, 5);
      expect(p.nome, 'Carlos');
      expect(p.conteudo, 'Viagem incrível!');
      expect(p.dataCriacao, '2026-06-01T10:00:00');
    });

    test('imagem e fotoPerfil opcionais são nulos', () {
      final p = Post.fromJson({
        'id_post': 2,
        'id_usuario': 1,
        'conteudo': 'Texto simples',
        'data_criacao': '2026-01-01T00:00:00',
      });
      expect(p.imagem, isNull);
      expect(p.fotoPerfil, isNull);
    });

    test('nome ausente assume string vazia', () {
      final p = Post.fromJson({
        'id_post': 3,
        'id_usuario': 1,
        'conteudo': 'Post sem nome',
        'data_criacao': '2026-01-01T00:00:00',
      });
      expect(p.nome, '');
    });

    test('campos de imagem presentes', () {
      final p = Post.fromJson({
        'id_post': 4,
        'id_usuario': 1,
        'nome': 'Ana',
        'conteudo': 'Foto da viagem',
        'imagem': 'https://cdn.test/img.jpg',
        'foto_perfil': 'https://cdn.test/perfil.jpg',
        'data_criacao': '2026-06-10T08:30:00',
      });
      expect(p.imagem, 'https://cdn.test/img.jpg');
      expect(p.fotoPerfil, 'https://cdn.test/perfil.jpg');
    });

    // ── Testes de robustez (resposta completa do backend pós-fix) ─────────────

    test('resposta completa do backend após criar post é desserializada sem crash', () {
      // Backend agora retorna objeto completo após POST /posts
      final p = Post.fromJson({
        'id_post': 10,
        'id_usuario': 2,
        'nome': 'Fernanda',
        'foto_perfil': 'https://cdn.test/f.jpg',
        'conteudo': 'Primeira postagem!',
        'imagem': null,
        'data_criacao': '2026-06-15T14:30:00',
      });
      expect(p.id, 10);
      expect(p.idUsuario, 2);
      expect(p.conteudo, 'Primeira postagem!');
      expect(p.imagem, isNull);
    });

    test('nome nulo no JSON usa fallback vazio', () {
      final p = Post.fromJson({
        'id_post': 5,
        'id_usuario': 3,
        'nome': null,
        'conteudo': 'Post sem nome explícito',
        'data_criacao': '2026-06-01T00:00:00',
      });
      expect(p.nome, '');
    });
  });
}
