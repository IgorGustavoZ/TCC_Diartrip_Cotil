from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator, Field
from datetime import datetime
from schemas import (
    GrupoLista, GrupoDetalhe, GrupoCriado, EntrarGrupoResponse,
    CodigoConviteResponse, MensagemResponse,
)
from utils.auth import get_usuario_logado
from utils.dependencies import verificar_admin_do_grupo
from utils.rate_limiter import verificar_rate_limit
from services import grupo_service

router = APIRouter()


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

    @field_validator("data_fim")
    @classmethod
    def validar_datas(cls, v: str, info) -> str:
        if "data_inicio" in info.data:
            inicio = datetime.strptime(info.data["data_inicio"], "%Y-%m-%d")
            fim = datetime.strptime(v, "%Y-%m-%d")
            if fim < inicio:
                raise ValueError("A data de fim não pode ser anterior à data de início")
        return v


class EntrarGrupoInput(BaseModel):
    codigo_convite: str


@router.get("/grupos", response_model=list[GrupoLista])
def listar_grupos(usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.listar_por_usuario(usuario_id)


@router.get("/gruposAll", response_model=list[GrupoLista])
def listar_grupos_all(usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.listar_por_usuario(usuario_id)


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


@router.put("/grupos/{id_grupo}", response_model=MensagemResponse,
            dependencies=[Depends(verificar_admin_do_grupo)])
def atualizar_grupo(id_grupo: int, dados: GrupoInput):
    return grupo_service.atualizar(id_grupo, dados)


@router.delete("/grupos/{id_grupo}", response_model=MensagemResponse)
def deletar_grupo(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.deletar(id_grupo, usuario_id)
