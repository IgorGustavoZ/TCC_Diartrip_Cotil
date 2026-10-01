from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel

class MensagemResponse(BaseModel):
    mensagem: str


class UsuarioSimples(BaseModel):
    id_usuario: int
    nome: str
    foto_perfil: Optional[str] = None

class UsuarioDesktop(BaseModel):
    id_usuario: int
    nome: str
    email: str
    data_criacao: Optional[datetime] = None

class UsuarioPublico(BaseModel):
    id_usuario: int
    nome: str
    bio: Optional[str] = None
    foto_perfil: Optional[str] = None
    data_criacao: Optional[datetime] = None
    seguidores: int = 0
    seguindo: int = 0
    ja_segue: Optional[bool] = None


class UsuarioMe(BaseModel):
    id_usuario: int
    nome: str
    email: str
    bio: Optional[str] = None
    foto_perfil: Optional[str] = None
    data_criacao: Optional[datetime] = None
    seguidores: int = 0
    seguindo: int = 0


class UsuarioCriado(BaseModel):
    mensagem: str
    id: int
    email: str


class FotoPerfilResponse(BaseModel):
    foto_perfil: str


class SeguirResponse(BaseModel):
    seguindo: bool
    total_seguidores: int


class LoginResponse(BaseModel):
    mensagem: str
    usuario_id: int


class TokenResponse(BaseModel):
    mensagem: str


class GrupoLista(BaseModel):
    id_grupo: int
    nome_grupo: str
    destino_principal: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    criador: str


class GrupoAdministradaResponse(GrupoLista):
    """Usado pelo seletor de "compartilhar roteiro" — além dos dados da
    viagem, diz quantos itens o roteiro dela já tem."""
    total_itens_roteiro: int = 0


class GrupoDetalhe(BaseModel):
    id_grupo: int
    nome_grupo: str
    destino_principal: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    orcamento: Optional[float] = None
    tipo_viagem: Optional[str] = None
    preferencias: Optional[str] = None
    criador_id: int
    criador: str
    codigo_convite: Optional[str] = None
    publica: bool = False
    limite_participantes: Optional[int] = None
    vagas_ocupadas: int = 0


class GrupoCriado(BaseModel):
    mensagem: str
    id_grupo: int
    codigo_convite: str


class CodigoConviteResponse(BaseModel):
    codigo_convite: str


class EntrarGrupoResponse(BaseModel):
    mensagem: str
    id_grupo: int


class MembroResponse(BaseModel):
    id_usuario: int
    nome: str
    foto_perfil: Optional[str] = None
    cargo: str


class GastoResponse(BaseModel):
    id_gasto: int
    valor: float
    categoria: Optional[str] = None
    descricao: Optional[str] = None
    data_gasto: date
    nome: str
    id_usuario: int


class GastoCriado(BaseModel):
    mensagem: str
    id: int


class BalancoItem(BaseModel):
    id_usuario: int
    nome: str
    saldo: float
    a_receber: float
    a_pagar: float


class RoteiroResponse(BaseModel):
    id_roteiro: int
    id_grupo: int
    titulo: str
    descricao: Optional[str] = None
    origem_ia: bool = False
    data_criacao: datetime


class RoteiroCriado(BaseModel):
    mensagem: str
    id: int


class FotoResponse(BaseModel):
    id_foto: int
    id_usuario: int
    caminho_arquivo: str
    template_usado: Optional[str] = None
    data_upload: datetime
    nome: str


class FotoCriada(BaseModel):
    mensagem: str
    url: str
    id_grupo: int


class ComentarioResponse(BaseModel):
    id: int
    id_post: int
    id_usuario: int
    conteudo: str
    data_criacao: datetime
    nome: str
    foto_perfil: Optional[str] = None


class PostRefGrupo(BaseModel):
    """Dados ATUAIS da viagem referenciada por uma publicação tipo='viagem'
    — lidos ao vivo de grupos_viagem, nunca copiados para o post."""
    id_grupo: int
    nome_grupo: str
    destino_principal: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    vagas_ocupadas: int = 0
    limite_participantes: Optional[int] = None


class RoteiroItemResumo(BaseModel):
    titulo: str
    descricao: Optional[str] = None


class PostRefRoteiro(BaseModel):
    """O ROTEIRO COMPLETO da viagem referenciada por uma publicação
    tipo='roteiro' — não existe um ID separado de "roteiro"; o conjunto de
    itens com este id_grupo JÁ É o roteiro completo, então a referência é a
    própria viagem. Itens lidos ao vivo de `roteiros`, nunca copiados."""
    id_grupo: int
    nome_grupo: str
    destino_principal: Optional[str] = None
    total_itens: int = 0
    itens: list[RoteiroItemResumo] = []


class PostResponse(BaseModel):
    id_post: int
    id_grupo: Optional[int] = None
    id_comunidade: Optional[int] = None
    tipo: str = "texto"
    conteudo: str
    imagem: Optional[str] = None
    data_criacao: datetime
    id_usuario: int
    nome: str
    foto_perfil: Optional[str] = None
    curtidas: int = 0
    ja_curtiu: int = 0
    comentarios: list[ComentarioResponse] = []
    ref_id_grupo: Optional[int] = None
    ref_id_roteiro: Optional[int] = None
    ref_grupo: Optional[PostRefGrupo] = None
    ref_roteiro: Optional[PostRefRoteiro] = None


class PostCriado(BaseModel):
    mensagem: str
    id_post: int


class CurtirResponse(BaseModel):
    curtiu: bool
    total_curtidas: int


class ChatIAResponse(BaseModel):
    pergunta: str
    resposta: str

class ChatIADesktop(BaseModel):
    id_chat: int
    id_usuario: int
    id_grupo: int
    pergunta: str
    resposta: Optional[str] = None
    data_interacao: datetime

class ChatIAHistorico(BaseModel):
    id_chat: int
    id_grupo: int
    pergunta: str
    resposta: Optional[str] = None
    data_interacao: datetime


class MensagemGrupoResponse(BaseModel):
    id_mensagem: int
    id_grupo: int
    id_usuario: int
    nome: str
    foto_perfil: Optional[str] = None
    conteudo: str
    data_envio: datetime


class CategoriaGasto(BaseModel):
    categoria: Optional[str] = None
    total: float
    qtd: int


class GastoRecente(BaseModel):
    valor: float
    categoria: Optional[str] = None
    descricao: Optional[str] = None
    data_gasto: Optional[date] = None


class RankingItem(BaseModel):
    nome: str
    total: float


class EstatisticasAdmin(BaseModel):
    membros_ativos: int
    total_fotos_subidas: int
    itens_no_roteiro: int


class DashboardAdmin(BaseModel):
    estatisticas: EstatisticasAdmin
    ranking_contribuicao_financeira: list[RankingItem]


class DashboardGeral(BaseModel):
    nome_grupo: str
    orcamento_total: float
    total_consumido: float
    orcamento_restante: float
    percentual_consumido: float
    distribuicao_categorias: list[CategoriaGasto]


class DashboardPessoal(BaseModel):
    total_pago_por_mim: float
    minha_divida_atual: float
    ultimos_gastos_pessoais: list[GastoRecente]
    meu_orcamento: Optional[float] = None
    disponivel: Optional[float] = None


class DashboardCompleto(BaseModel):
    geral: DashboardGeral
    pessoal: DashboardPessoal
    admin: Optional[DashboardAdmin] = None


# --- Explorar Viagens (catálogo de viagens públicas) ----------------------

class ExplorarViagemResponse(BaseModel):
    id_grupo: int
    nome_grupo: str
    destino_principal: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    id_criador: int
    criador: str
    limite_participantes: int
    vagas_ocupadas: int = 0
    orcamento_total: Optional[float] = None


class SolicitacaoResponse(BaseModel):
    id_solicitacao: int
    id_grupo: int
    nome_grupo: str
    id_usuario_solicitante: int
    nome: str
    foto_perfil: Optional[str] = None
    mensagem: Optional[str] = None
    orcamento: Optional[float] = None
    status: str
    data_solicitacao: datetime


class SolicitacaoCriada(BaseModel):
    mensagem: str
    id_solicitacao: int


class ComunidadeResponse(BaseModel):
    """Uma comunidade NÃO é uma viagem: sem datas, sem roteiro — é um grupo
    temático (ex.: "Amantes do Japão"), reaproveitando o mesmo molde de
    grupos_viagem/grupo_membros (cargo admin/membro) como entidade própria."""
    id_comunidade: int
    nome: str
    descricao: Optional[str] = None
    foto_capa: Optional[str] = None
    categoria: Optional[str] = None
    privacidade: str
    criado_por: int
    criador: str
    total_membros: int = 0
    sou_membro: bool = False
    meu_cargo: Optional[str] = None


class ComunidadeCriada(BaseModel):
    mensagem: str
    id_comunidade: int


class FotoComunidadeResponse(BaseModel):
    foto_capa: str
