from fastapi import APIRouter, Depends
from pydantic import BaseModel
from utils.auth import get_usuario_logado
from services import chat_service

router = APIRouter()


class ChatInput(BaseModel):
    pergunta: str
    id_grupo: int


@router.get("/chat")
def listar_chat(usuario_id: int = Depends(get_usuario_logado)):
    return chat_service.listar(usuario_id)


@router.post("/chat")
def criar_chat(dados: ChatInput, usuario_id: int = Depends(get_usuario_logado)):
    return chat_service.criar(dados.pergunta, dados.id_grupo, usuario_id)
