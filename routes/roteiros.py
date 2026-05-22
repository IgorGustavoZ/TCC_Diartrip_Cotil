from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from utils.auth import get_usuario_logado
from services import roteiro_service

router = APIRouter(tags=["Roteiros"])


class RoteiroInput(BaseModel):
    id_grupo: int
    titulo: str = Field(..., max_length=200)
    descricao: str = Field(..., max_length=10000)


class RoteiroUpdate(BaseModel):
    titulo: str = Field(..., max_length=200)
    descricao: str = Field(..., max_length=10000)


@router.get("/grupos/{id_grupo}/roteiros")
def listar_roteiros_grupo(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return roteiro_service.listar_por_grupo(id_grupo, usuario_id)


@router.get("/roteiros")
def listar_roteiros(usuario_id: int = Depends(get_usuario_logado)):
    return roteiro_service.listar_por_usuario(usuario_id)


@router.get("/roteiros/{id_roteiro}")
def buscar_roteiro(id_roteiro: int, usuario_id: int = Depends(get_usuario_logado)):
    return roteiro_service.buscar_por_id(id_roteiro, usuario_id)


@router.post("/roteiros")
def criar_roteiro(dados: RoteiroInput, usuario_id: int = Depends(get_usuario_logado)):
    return roteiro_service.criar(dados, usuario_id)


@router.put("/roteiros/{id_roteiro}")
def atualizar_roteiro(
    id_roteiro: int, dados: RoteiroUpdate, usuario_id: int = Depends(get_usuario_logado)
):
    return roteiro_service.atualizar(id_roteiro, dados, usuario_id)


@router.delete("/roteiros/{id_roteiro}")
def deletar_roteiro(id_roteiro: int, usuario_id: int = Depends(get_usuario_logado)):
    return roteiro_service.deletar(id_roteiro, usuario_id)
