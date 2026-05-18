from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from datetime import datetime
from utils.auth import get_usuario_logado
from utils.dependencies import verificar_admin_do_grupo
from services import grupo_service

router = APIRouter()


class GrupoInput(BaseModel):
    nome_grupo: str
    destino_principal: str
    data_inicio: str
    data_fim: str
    orcamento: float
    tipo_viagem: str
    preferencias: str

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


@router.get("/grupos")
def listar_grupos(usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.listar_por_usuario(usuario_id)


@router.get("/grupos/buscar")
def buscar_grupo_por_nome(
    nome: str | None = Query(None),
    usuario_id: int = Depends(get_usuario_logado),
):
    return grupo_service.buscar_por_nome(usuario_id, nome)


@router.post("/grupos/entrar")
def entrar_por_codigo(dados: EntrarGrupoInput, usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.entrar_por_codigo(dados.codigo_convite, usuario_id)


@router.get("/grupos/{id_grupo}")
def buscar_grupo_por_id(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.buscar_por_id(id_grupo, usuario_id)


@router.post("/grupos")
def criar_grupo(dados: GrupoInput, usuario_id: int = Depends(get_usuario_logado)):
    return grupo_service.criar(dados, usuario_id)


@router.put("/grupos/{id_grupo}", dependencies=[Depends(verificar_admin_do_grupo)])
def atualizar_grupo(id_grupo: int, dados: GrupoInput):
    return grupo_service.atualizar(id_grupo, dados)


@router.delete("/grupos/{id_grupo}", dependencies=[Depends(verificar_admin_do_grupo)])
def deletar_grupo(id_grupo: int):
    return grupo_service.deletar(id_grupo)
