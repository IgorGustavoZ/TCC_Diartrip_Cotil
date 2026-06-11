class Grupo {
  final int id;
  final String nomeGrupo;
  final String destinoPrincipal;
  final String? dataInicio;
  final String? dataFim;
  final double? orcamento;
  final String? tipoViagem;
  final String? preferencias;
  final String? codigoConvite;
  final int? criadorId;

  const Grupo({
    required this.id,
    required this.nomeGrupo,
    required this.destinoPrincipal,
    this.dataInicio,
    this.dataFim,
    this.orcamento,
    this.tipoViagem,
    this.preferencias,
    this.codigoConvite,
    this.criadorId,
  });

  factory Grupo.fromJson(Map<String, dynamic> j) => Grupo(
        id: j['id_grupo'] as int,
        nomeGrupo: j['nome_grupo'] as String,
        destinoPrincipal: j['destino_principal'] as String,
        dataInicio: j['data_inicio'] as String?,
        dataFim: j['data_fim'] as String?,
        orcamento: (j['orcamento'] as num?)?.toDouble(),
        tipoViagem: j['tipo_viagem'] as String?,
        preferencias: j['preferencias'] as String?,
        codigoConvite: j['codigo_convite'] as String?,
        criadorId: j['criador_id'] as int?,
      );
}

class Membro {
  final int id;
  final String nome;
  final String? fotoPerfil;
  final String cargo;

  const Membro({
    required this.id,
    required this.nome,
    this.fotoPerfil,
    required this.cargo,
  });

  factory Membro.fromJson(Map<String, dynamic> j) => Membro(
        id: j['id_usuario'] as int,
        nome: j['nome'] as String,
        fotoPerfil: j['foto_perfil'] as String?,
        cargo: j['cargo'] as String,
      );

  bool get isAdmin => cargo == 'admin';
}
