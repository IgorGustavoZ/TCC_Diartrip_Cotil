import 'package:flutter_test/flutter_test.dart';
import 'package:diartrip_flutter/models/mensagem.dart';

void main() {
  group('Mensagem.fromJson', () {
    test('campos obrigatórios mapeados', () {
      final m = Mensagem.fromJson({
        'id_mensagem': 1,
        'id_usuario': 3,
        'id_grupo': 10,
        'nome': 'Pedro',
        'conteudo': 'Oi pessoal!',
        'data_envio': '2026-06-01T20:00:00',
      });
      expect(m.id, 1);
      expect(m.idUsuario, 3);
      expect(m.idGrupo, 10);
      expect(m.nome, 'Pedro');
      expect(m.conteudo, 'Oi pessoal!');
      expect(m.dataEnvio, '2026-06-01T20:00:00');
    });

    test('fotoPerfil nulo quando ausente', () {
      final m = Mensagem.fromJson({
        'id_mensagem': 2,
        'id_usuario': 1,
        'id_grupo': 5,
        'nome': 'X',
        'conteudo': 'Olá',
        'data_envio': '2026-06-01T10:00:00',
      });
      expect(m.fotoPerfil, isNull);
    });

    test('id_grupo ausente assume zero', () {
      final m = Mensagem.fromJson({
        'id_mensagem': 3,
        'id_usuario': 1,
        'nome': 'Y',
        'conteudo': 'Teste',
        'data_envio': '2026-06-01T10:00:00',
      });
      expect(m.idGrupo, 0);
    });

    test('nome ausente assume string vazia', () {
      final m = Mensagem.fromJson({
        'id_mensagem': 4,
        'id_usuario': 1,
        'id_grupo': 1,
        'conteudo': 'Hi',
        'data_envio': '2026-06-01T10:00:00',
      });
      expect(m.nome, '');
    });

    test('fotoPerfil presente', () {
      final m = Mensagem.fromJson({
        'id_mensagem': 5,
        'id_usuario': 2,
        'id_grupo': 1,
        'nome': 'Z',
        'foto_perfil': 'https://cdn.test/p.jpg',
        'conteudo': 'Cheers',
        'data_envio': '2026-06-01T10:00:00',
      });
      expect(m.fotoPerfil, 'https://cdn.test/p.jpg');
    });

    test('resposta completa do backend após enviar mensagem é desserializada sem crash', () {
      // Backend agora retorna objeto completo após POST /grupos/{id}/chat
      final m = Mensagem.fromJson({
        'id_mensagem': 99,
        'id_grupo': 10,
        'id_usuario': 1,
        'nome': 'Alice',
        'foto_perfil': null,
        'conteudo': 'Boa viagem!',
        'data_envio': '2026-07-01T08:00:00',
      });
      expect(m.id, 99);
      expect(m.idGrupo, 10);
      expect(m.idUsuario, 1);
      expect(m.conteudo, 'Boa viagem!');
    });
  });
}
