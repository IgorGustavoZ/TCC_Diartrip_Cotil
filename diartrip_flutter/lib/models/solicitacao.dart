/// Pedido de participação numa viagem pública (Explorar Viagens), visto pelo
/// admin do grupo. Espelha `SolicitacaoResponse` em backend/schemas.py.
class Solicitacao {
  final int id;
  final int idGrupo;
  final String nomeGrupo;
  final int idUsuarioSolicitante;
  final String nome;
  final String? fotoPerfil;
  final String? mensagem;
  final double? orcamento;
  final String status;
  final String dataSolicitacao;

  const Solicitacao({
    required this.id,
    required this.idGrupo,
    required this.nomeGrupo,
    required this.idUsuarioSolicitante,
    required this.nome,
    this.fotoPerfil,
    this.mensagem,
    this.orcamento,
    required this.status,
    required this.dataSolicitacao,
  });

  factory Solicitacao.fromJson(Map<String, dynamic> j) => Solicitacao(
        id: j['id_solicitacao'] as int,
        idGrupo: j['id_grupo'] as int,
        nomeGrupo: j['nome_grupo'] as String? ?? '',
        idUsuarioSolicitante: j['id_usuario_solicitante'] as int,
        nome: j['nome'] as String? ?? '',
        fotoPerfil: j['foto_perfil'] as String?,
        mensagem: j['mensagem'] as String?,
        orcamento: (j['orcamento'] as num?)?.toDouble(),
        status: j['status'] as String? ?? 'pendente',
        dataSolicitacao: j['data_solicitacao'] as String? ?? '',
      );
}
