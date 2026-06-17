class Mensagem {
  final int id;
  final int idUsuario;
  final int idGrupo;
  final String nome;
  final String? fotoPerfil;
  final String conteudo;
  final String dataEnvio;

  const Mensagem({
    required this.id,
    required this.idUsuario,
    required this.idGrupo,
    required this.nome,
    this.fotoPerfil,
    required this.conteudo,
    required this.dataEnvio,
  });

  factory Mensagem.fromJson(Map<String, dynamic> j) => Mensagem(
        id: j['id_mensagem'] as int,
        idUsuario: j['id_usuario'] as int,
        idGrupo: j['id_grupo'] as int? ?? 0,
        nome: j['nome'] as String? ?? '',
        fotoPerfil: j['foto_perfil'] as String?,
        conteudo: j['conteudo'] as String,
        dataEnvio: j['data_envio'] as String,
      );
}
