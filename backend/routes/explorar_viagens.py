from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from schemas import ExplorarViagemResponse, SolicitacaoResponse, SolicitacaoCriada, MensagemResponse
from utils.auth import get_usuario_logado
from utils.dependencies import verificar_admin_do_grupo
from utils.rate_limiter import verificar_rate_limit
from services import explorar_viagens_service

router = APIRouter()


class PublicarInput(BaseModel):
    publica: bool
    limite_participantes: Optional[int] = Field(None, ge=1)


class SolicitarInput(BaseModel):
    mensagem: Optional[str] = Field(None, max_length=500)
    orcamento: Optional[float] = Field(None, ge=0)


@router.put(
    "/grupos/{id_grupo}/publicar",
    response_model=MensagemResponse,
    dependencies=[Depends(verificar_admin_do_grupo)],
)
def publicar_viagem(id_grupo: int, dados: PublicarInput):
    return explorar_viagens_service.publicar(id_grupo, dados.publica, dados.limite_participantes)


@router.get("/explorar", response_model=list[ExplorarViagemResponse])
def listar_explorar(
    destino: str | None = Query(None, max_length=150),
    limite: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"explorar_buscar:{usuario_id}", limite=30)
    return explorar_viagens_service.listar_publicas(destino, limite, offset)


@router.get("/explorar/{id_grupo}", response_model=ExplorarViagemResponse)
def detalhar_explorar(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return explorar_viagens_service.detalhar_publica(id_grupo)


@router.post("/explorar/{id_grupo}/solicitar", response_model=SolicitacaoCriada)
def solicitar_participacao(
    id_grupo: int,
    dados: SolicitarInput,
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"explorar_solicitar:{usuario_id}", limite=10)
    return explorar_viagens_service.solicitar(id_grupo, usuario_id, dados.mensagem, dados.orcamento)


@router.get(
    "/grupos/{id_grupo}/solicitacoes",
    response_model=list[SolicitacaoResponse],
    dependencies=[Depends(verificar_admin_do_grupo)],
)
def listar_solicitacoes_grupo(id_grupo: int):
    return explorar_viagens_service.listar_solicitacoes(id_grupo)


@router.put("/solicitacoes/{id_solicitacao}/aceitar", response_model=MensagemResponse)
def aceitar_solicitacao(id_solicitacao: int, usuario_id: int = Depends(get_usuario_logado)):
    return explorar_viagens_service.aceitar_solicitacao(id_solicitacao, usuario_id)


@router.put("/solicitacoes/{id_solicitacao}/recusar", response_model=MensagemResponse)
def recusar_solicitacao(id_solicitacao: int, usuario_id: int = Depends(get_usuario_logado)):
    return explorar_viagens_service.recusar_solicitacao(id_solicitacao, usuario_id)
