class Roteiro {
  final int id;
  final int idGrupo;
  final String titulo;
  final String descricao;

  const Roteiro({
    required this.id,
    required this.idGrupo,
    required this.titulo,
    required this.descricao,
  });

  factory Roteiro.fromJson(Map<String, dynamic> j) => Roteiro(
        id: j['id_roteiro'] as int,
        idGrupo: j['id_grupo'] as int,
        titulo: j['titulo'] as String,
        descricao: j['descricao'] as String? ?? '',
      );
}
