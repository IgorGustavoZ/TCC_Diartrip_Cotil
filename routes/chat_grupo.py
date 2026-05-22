from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from utils.auth import get_usuario_logado
from services import chat_grupo_service

router = APIRouter(tags=["Chat Grupo"])


class MensagemInput(BaseModel):
    conteudo: str = Field(..., min_length=1, max_length=2000)


@router.get("/grupos/{id_grupo}/chat")
def listar_mensagens(
    id_grupo: int,
    since_id: int = Query(0),
    usuario_id: int = Depends(get_usuario_logado),
):
    return chat_grupo_service.listar(id_grupo, usuario_id, since_id)


@router.post("/grupos/{id_grupo}/chat")
def enviar_mensagem(
    id_grupo: int, dados: MensagemInput, usuario_id: int = Depends(get_usuario_logado)
):
    return chat_grupo_service.enviar(id_grupo, usuario_id, dados.conteudo)
