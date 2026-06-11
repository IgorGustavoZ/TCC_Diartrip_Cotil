class CategoriaGasto {
  final String categoria;
  final double total;
  const CategoriaGasto({required this.categoria, required this.total});
  factory CategoriaGasto.fromJson(Map<String, dynamic> j) => CategoriaGasto(
        categoria: j['categoria'] as String,
        total: (j['total'] as num).toDouble(),
      );
}

class GastoResumido {
  final String descricao;
  final String categoria;
  final double valor;
  final String dataGasto;
  const GastoResumido({
    required this.descricao,
    required this.categoria,
    required this.valor,
    required this.dataGasto,
  });
  factory GastoResumido.fromJson(Map<String, dynamic> j) => GastoResumido(
        descricao: j['descricao'] as String? ?? '',
        categoria: j['categoria'] as String,
        valor: (j['valor'] as num).toDouble(),
        dataGasto: j['data_gasto'] as String? ?? '',
      );
}

class RankingItem {
  final String nome;
  final double total;
  const RankingItem({required this.nome, required this.total});
  factory RankingItem.fromJson(Map<String, dynamic> j) => RankingItem(
        nome: j['nome'] as String,
        total: (j['total'] as num).toDouble(),
      );
}

class Estatisticas {
  final int membrosAtivos;
  final int totalFotosSubidas;
  final int itensNoRoteiro;
  const Estatisticas({
    required this.membrosAtivos,
    required this.totalFotosSubidas,
    required this.itensNoRoteiro,
  });
  factory Estatisticas.fromJson(Map<String, dynamic> j) => Estatisticas(
        membrosAtivos: j['membros_ativos'] as int? ?? 0,
        totalFotosSubidas: j['total_fotos_subidas'] as int? ?? 0,
        itensNoRoteiro: j['itens_no_roteiro'] as int? ?? 0,
      );
}

class DashboardGeral {
  final double totalConsumido;
  final double orcamentoRestante;
  final int percentualConsumido;
  final List<CategoriaGasto> distribuicao;

  const DashboardGeral({
    required this.totalConsumido,
    required this.orcamentoRestante,
    required this.percentualConsumido,
    required this.distribuicao,
  });

  factory DashboardGeral.fromJson(Map<String, dynamic> j) => DashboardGeral(
        totalConsumido: (j['total_consumido'] as num).toDouble(),
        orcamentoRestante: (j['orcamento_restante'] as num).toDouble(),
        percentualConsumido: (j['percentual_consumido'] as num?)?.toInt() ?? 0,
        distribuicao: (j['distribuicao_categorias'] as List? ?? [])
            .map((e) => CategoriaGasto.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class DashboardPessoal {
  final double totalPagoPorMim;
  final double minhaDividaAtual;
  final List<GastoResumido> ultimosGastos;

  const DashboardPessoal({
    required this.totalPagoPorMim,
    required this.minhaDividaAtual,
    required this.ultimosGastos,
  });

  factory DashboardPessoal.fromJson(Map<String, dynamic> j) => DashboardPessoal(
        totalPagoPorMim: (j['total_pago_por_mim'] as num).toDouble(),
        minhaDividaAtual: (j['minha_divida_atual'] as num).toDouble(),
        ultimosGastos: (j['ultimos_gastos_pessoais'] as List? ?? [])
            .map((e) => GastoResumido.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class DashboardAdmin {
  final List<RankingItem> ranking;
  final Estatisticas estatisticas;

  const DashboardAdmin({required this.ranking, required this.estatisticas});

  factory DashboardAdmin.fromJson(Map<String, dynamic> j) => DashboardAdmin(
        ranking: (j['ranking_contribuicao_financeira'] as List? ?? [])
            .map((e) => RankingItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        estatisticas: Estatisticas.fromJson(
          j['estatisticas'] as Map<String, dynamic>? ?? {},
        ),
      );
}

class DashboardCompleto {
  final DashboardGeral geral;
  final DashboardPessoal pessoal;
  final DashboardAdmin? admin;

  const DashboardCompleto({
    required this.geral,
    required this.pessoal,
    this.admin,
  });

  factory DashboardCompleto.fromJson(Map<String, dynamic> j) => DashboardCompleto(
        geral: DashboardGeral.fromJson(j['geral'] as Map<String, dynamic>),
        pessoal: DashboardPessoal.fromJson(j['pessoal'] as Map<String, dynamic>),
        admin: j['admin'] != null
            ? DashboardAdmin.fromJson(j['admin'] as Map<String, dynamic>)
            : null,
      );
}
