class Comentario {
  final int id;
  final int idPost;
  final int idUsuario;
  final String nome;
  final String? fotoPerfil;
  final String conteudo;
  final String dataCriacao;

  const Comentario({
    required this.id,
    required this.idPost,
    required this.idUsuario,
    required this.nome,
    this.fotoPerfil,
    required this.conteudo,
    required this.dataCriacao,
  });

  factory Comentario.fromJson(Map<String, dynamic> j) => Comentario(
        id: j['id'] as int,
        idPost: j['id_post'] as int,
        idUsuario: j['id_usuario'] as int,
        nome: j['nome'] as String? ?? '',
        fotoPerfil: j['foto_perfil'] as String?,
        conteudo: j['conteudo'] as String,
        dataCriacao: j['data_criacao'] as String,
      );
}
