from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator, Field
from datetime import datetime, date
from schemas import (
    GrupoLista, GrupoDetalhe, GrupoCriado, EntrarGrupoResponse,
    CodigoConviteResponse, MensagemResponse,
)
from utils.auth import get_usuario_logado
from utils.rate_limiter import verificar_rate_limit
from services import grupo_service, membro_service

router = APIRouter()


def _validar_datas_consistentes(v: str, info) -> str:
    """fim tem que ser estritamente depois do início (viagem de 1 dia com
    início=fim não é aceita, mantendo o mesmo comportamento que o formulário
    de criação já tinha no frontend)."""
    if "data_inicio" in info.data:
        inicio = datetime.strptime(info.data["data_inicio"], "%Y-%m-%d")
        fim = datetime.strptime(v, "%Y-%m-%d")
        if fim <= inicio:
            raise ValueError("A data de fim deve ser posterior à data de início")
    return v


def _validar_nao_passado(v: str) -> str:
    if datetime.strptime(v, "%Y-%m-%d").date() < date.today():
        raise ValueError("A data não pode ser anterior a hoje")
    return v


class GrupoInput(BaseModel):
    nome_grupo: str = Field(..., max_length=100)
    destino_principal: str = Field(..., max_length=150)
    data_inicio: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    data_fim: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    orcamento: float
    tipo_viagem: str = Field(..., max_length=100)
    preferencias: str = Field(..., max_length=1000)

    @field_validator("orcamento")
    @classmethod
    def orcamento_positivo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("O orçamento não pode ser negativo")
        return v

    # Viagem nova: as duas datas são sempre "novas", então já valem a regra
    # de "não pode ser no passado" direto no schema.
    @field_validator("data_inicio")
    @classmethod
    def validar_inicio_futuro(cls, v: str) -> str:
        return _validar_nao_passado(v)

    @field_validator("data_fim")
    @classmethod
    def validar_datas(cls, v: str, info) -> str:
        _validar_nao_passado(v)
        return _validar_datas_consistentes(v, info)


class GrupoAtualizarInput(BaseModel):
    """Igual a GrupoInput, mas sem orçamento — o orçamento total deixou de
    ser um campo editável diretamente, é sempre a soma dos orçamentos
    individuais dos participantes (ver PATCH /grupos/{id}/meu-orcamento).

    Aqui NÃO validamos "não pode ser no passado" no schema: numa edição, as
    datas podem já existir e estar no passado (viagem em andamento/concluída)
    sem que a pessoa esteja mexendo nelas. Essa checagem — só quando a data
    realmente muda — é feita em grupo_service.atualizar(), que tem acesso ao
    valor atual salvo no banco para comparar."""
    nome_grupo: str = Field(..., max_length=100)
    destino_principal: str = Field(..., max_length=150)
    data_inicio: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    data_fim: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    tipo_viagem: str = Field(..., max_length=100)
    preferencias: str = Field(..., max_length=1000)

    @field_validator("data_fim")
    @classmethod
    def validar_datas(cls, v: str, info) -> str:
        return _validar_datas_consistentes(v, info)


class AlterarMeuOrcamentoInput(BaseModel):
    orcamento: float = Field(..., ge=0)


class EntrarGrupoInput(BaseModel):
    codigo_convite: str


@router.get("/grupos/", response_model=list[GrupoLista])
def listar_grupos(usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.listar_tudo()


# @router.get("/gruposAll", response_model=list[GrupoLista])
# def listar_grupos_all(usuario_id: int = Depends(get_usuario_logado)):
#     return grupo_service.listar_por_usuario(usuario_id)


@router.get("/grupos/buscar", response_model=list[GrupoLista])
def buscar_grupo_por_nome(
    nome: str | None = Query(None, max_length=100),
    limite: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"busca_grupos:{usuario_id}", limite=30)
    return grupo_service.buscar_por_nome(usuario_id, nome, limite, offset)


@router.post("/grupos/entrar", response_model=EntrarGrupoResponse)
def entrar_por_codigo(dados: EntrarGrupoInput, usuario_id: int = Depends(get_usuario_logado)):
    verificar_rate_limit(f"convite:{usuario_id}", limite=10)
    return grupo_service.entrar_por_codigo(dados.codigo_convite, usuario_id)


@router.get("/grupos/{id_grupo}", response_model=GrupoDetalhe)
def buscar_grupo_por_id(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.buscar_por_id(id_grupo, usuario_id)


@router.get("/grupos/{id_grupo}/codigo-convite", response_model=CodigoConviteResponse)
def obter_codigo_convite(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.obter_codigo_convite(id_grupo, usuario_id)


@router.post("/grupos/{id_grupo}/rotacionar-convite", response_model=CodigoConviteResponse)
def rotacionar_codigo_convite(
    id_grupo: int,
    days: int = Query(7, ge=1, le=365, description="Validade do novo código em dias"),
    usuario_id: int = Depends(get_usuario_logado),
):
    return grupo_service.rotacionar_codigo_convite(id_grupo, usuario_id, days)


@router.post("/grupos", response_model=GrupoCriado, status_code=201)
def criar_grupo(dados: GrupoInput, usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.criar(dados, usuario_id)


@router.put("/grupos/{id_grupo}", response_model=MensagemResponse)
def atualizar_grupo(
    id_grupo: int, dados: GrupoAtualizarInput, usuario_id: int = Depends(get_usuario_logado)
):
    return grupo_service.atualizar(id_grupo, dados, usuario_id)


@router.patch("/grupos/{id_grupo}/meu-orcamento", response_model=MensagemResponse)
def alterar_meu_orcamento(
    id_grupo: int, dados: AlterarMeuOrcamentoInput, usuario_id: int = Depends(get_usuario_logado)
):
    return membro_service.alterar_meu_orcamento(id_grupo, usuario_id, dados.orcamento)


@router.delete("/grupos/{id_grupo}", response_model=MensagemResponse)
def deletar_grupo(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.deletar(id_grupo, usuario_id)
