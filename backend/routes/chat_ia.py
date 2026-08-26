from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from schemas import ChatIAResponse, ChatIAHistorico
from utils.auth import get_usuario_logado
from services import chat_service

router = APIRouter()


class ChatInput(BaseModel):
    pergunta: str = Field(..., min_length=1, max_length=1000)
    id_grupo: int


@router.get("/chat/all", response_model=list[ChatIAHistorico])
def listar_todos_os_chats(
    usuario_id: int = Depends(get_usuario_logado),
):
    return chat_service.listar_tudo()


@router.get("/chat", response_model=list[ChatIAHistorico])
def listar_chat(
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    usuario_id: int = Depends(get_usuario_logado),
):
    return chat_service.listar(usuario_id, limite, offset)


@router.post("/chat", response_model=ChatIAResponse)
def criar_chat(dados: ChatInput, usuario_id: int = Depends(get_usuario_logado)):
    return chat_service.criar(dados.pergunta, dados.id_grupo, usuario_id)
