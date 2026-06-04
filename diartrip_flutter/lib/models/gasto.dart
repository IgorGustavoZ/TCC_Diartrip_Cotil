class Gasto {
  final int id;
  final int idGrupo;
  final int idUsuario;
  final String nomeUsuario;
  final double valor;
  final String categoria;
  final String? descricao;
  final String? dataGasto;
  final List<int> idUsuariosDivisao;

  const Gasto({
    required this.id,
    required this.idGrupo,
    required this.idUsuario,
    required this.nomeUsuario,
    required this.valor,
    required this.categoria,
    this.descricao,
    this.dataGasto,
    this.idUsuariosDivisao = const [],
  });

  factory Gasto.fromJson(Map<String, dynamic> j) => Gasto(
        id: j['id_gasto'] as int,
        idGrupo: j['id_grupo'] as int? ?? 0,
        idUsuario: j['id_usuario'] as int,
        nomeUsuario: j['nome'] as String? ?? '',
        valor: (j['valor'] as num).toDouble(),
        categoria: j['categoria'] as String,
        descricao: j['descricao'] as String?,
        dataGasto: j['data_gasto'] as String?,
        idUsuariosDivisao: (j['id_usuarios_divisao'] as List?)
                ?.map((e) => e as int)
                .toList() ??
            [],
      );
}
