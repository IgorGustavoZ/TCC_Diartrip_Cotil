/// Trip listed in "Explore Trips" — matches `ExplorarViagemResponse` on the
/// backend (GET /explorar), a public trip open for join requests.
class ViagemExplorar {
  final int id;
  final String nomeGrupo;
  final String? destinoPrincipal;
  final String? dataInicio;
  final String? dataFim;
  final int idCriador;
  final String criador;
  final int limiteParticipantes;
  final int vagasOcupadas;
  final double? orcamentoTotal;

  const ViagemExplorar({
    required this.id,
    required this.nomeGrupo,
    this.destinoPrincipal,
    this.dataInicio,
    this.dataFim,
    required this.idCriador,
    required this.criador,
    required this.limiteParticipantes,
    required this.vagasOcupadas,
    this.orcamentoTotal,
  });

  bool get cheia => vagasOcupadas >= limiteParticipantes;

  factory ViagemExplorar.fromJson(Map<String, dynamic> j) => ViagemExplorar(
        id: j['id_grupo'] as int,
        nomeGrupo: j['nome_grupo'] as String,
        destinoPrincipal: j['destino_principal'] as String?,
        dataInicio: j['data_inicio'] as String?,
        dataFim: j['data_fim'] as String?,
        idCriador: j['id_criador'] as int,
        criador: j['criador'] as String,
        limiteParticipantes: j['limite_participantes'] as int,
        vagasOcupadas: (j['vagas_ocupadas'] as num?)?.toInt() ?? 0,
        orcamentoTotal: (j['orcamento_total'] as num?)?.toDouble(),
      );
}
