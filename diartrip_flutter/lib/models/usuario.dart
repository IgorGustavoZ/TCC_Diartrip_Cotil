class Usuario {
  final int id;
  final String nome;
  final String? email;
  final String? bio;
  final String? fotoPerfil;
  final String? dataCriacao;
  final int seguidores;
  final int seguindo;
  final bool? jaSegue;

  const Usuario({
    required this.id,
    required this.nome,
    this.email,
    this.bio,
    this.fotoPerfil,
    this.dataCriacao,
    this.seguidores = 0,
    this.seguindo = 0,
    this.jaSegue,
  });

  factory Usuario.fromJson(Map<String, dynamic> j) => Usuario(
        id: j['id_usuario'] as int,
        nome: j['nome'] as String,
        email: j['email'] as String?,
        bio: j['bio'] as String?,
        fotoPerfil: j['foto_perfil'] as String?,
        dataCriacao: j['data_criacao'] as String?,
        seguidores: (j['seguidores'] as num?)?.toInt() ?? 0,
        seguindo: (j['seguindo'] as num?)?.toInt() ?? 0,
        jaSegue: j['ja_segue'] as bool?,
      );

  String get iniciais {
    final parts = nome.trim().split(' ');
    if (parts.length >= 2) return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    return nome.isNotEmpty ? nome[0].toUpperCase() : '?';
  }
}
