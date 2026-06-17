from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from schemas import MembroResponse, MensagemResponse
from utils.auth import get_usuario_logado
from services import membro_service

router = APIRouter()


class MembroInput(BaseModel):
    id_usuario_novo: int


@router.get("/grupos/{id_grupo}/membros", response_model=list[MembroResponse])
def listar_membros(
    id_grupo: int,
    limite: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    usuario_id: int = Depends(get_usuario_logado),
):
    return membro_service.listar(id_grupo, usuario_id, limite, offset)


@router.post("/grupos/{id_grupo}/membros", response_model=MensagemResponse)
def adicionar_membro(
    id_grupo: int, dados: MembroInput, usuario_id: int = Depends(get_usuario_logado)
):
    return membro_service.adicionar(id_grupo, dados.id_usuario_novo, usuario_id)


@router.delete("/grupos/{id_grupo}/membros/{id_usuario_remover}", response_model=MensagemResponse)
def remover_membro(
    id_grupo: int, id_usuario_remover: int, usuario_id: int = Depends(get_usuario_logado)
):
    return membro_service.remover(id_grupo, id_usuario_remover, usuario_id)


@router.put("/grupos/{id_grupo}/membros/{id_usuario_promover}/promover",
            response_model=MensagemResponse)
def promover_admin(
    id_grupo: int, id_usuario_promover: int, usuario_id: int = Depends(get_usuario_logado)
):
    return membro_service.promover(id_grupo, id_usuario_promover, usuario_id)


@router.put("/grupos/{id_grupo}/membros/{id_usuario_rebaixar}/rebaixar",
            response_model=MensagemResponse)
def rebaixar_para_membro(
    id_grupo: int, id_usuario_rebaixar: int, usuario_id: int = Depends(get_usuario_logado)
):
    return membro_service.rebaixar(id_grupo, id_usuario_rebaixar, usuario_id)


@router.delete("/grupos/{id_grupo}/sair", response_model=MensagemResponse)
def sair_grupo(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return membro_service.sair(id_grupo, usuario_id)
