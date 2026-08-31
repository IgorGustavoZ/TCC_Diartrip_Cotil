class Roteiro {
  final int id;
  final int idGrupo;
  final String titulo;
  final String descricao;
  final bool origemIa;

  const Roteiro({
    required this.id,
    required this.idGrupo,
    required this.titulo,
    required this.descricao,
    this.origemIa = false,
  });

  factory Roteiro.fromJson(Map<String, dynamic> j) => Roteiro(
        id: j['id_roteiro'] as int,
        idGrupo: j['id_grupo'] as int,
        titulo: j['titulo'] as String,
        descricao: j['descricao'] as String? ?? '',
        origemIa: j['origem_ia'] as bool? ?? false,
      );
}
