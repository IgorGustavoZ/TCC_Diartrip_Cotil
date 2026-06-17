import 'comentario.dart';

class Post {
  final int id;
  final int idUsuario;
  final String nome;
  final String? fotoPerfil;
  final String conteudo;
  final String? imagem;
  final String dataCriacao;
  final int curtidas;
  final bool jaCurtiu;
  final List<Comentario> comentarios;

  const Post({
    required this.id,
    required this.idUsuario,
    required this.nome,
    this.fotoPerfil,
    required this.conteudo,
    this.imagem,
    required this.dataCriacao,
    this.curtidas = 0,
    this.jaCurtiu = false,
    this.comentarios = const [],
  });

  factory Post.fromJson(Map<String, dynamic> j) => Post(
        id: j['id_post'] as int,
        idUsuario: j['id_usuario'] as int,
        nome: j['nome'] as String? ?? '',
        fotoPerfil: j['foto_perfil'] as String?,
        conteudo: j['conteudo'] as String,
        imagem: j['imagem'] as String?,
        dataCriacao: j['data_criacao'] as String,
        curtidas: (j['curtidas'] as num?)?.toInt() ?? 0,
        jaCurtiu: (j['ja_curtiu'] as dynamic) == true ||
            (j['ja_curtiu'] as dynamic) == 1,
        comentarios: (j['comentarios'] as List<dynamic>?)
                ?.map((e) => Comentario.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
      );
}
