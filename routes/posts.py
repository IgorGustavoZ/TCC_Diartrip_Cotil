import os
from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional
from utils.auth import get_usuario_logado
from services import post_service

router = APIRouter()


@router.get("/posts/usuario/{alvo_id}")
def posts_do_usuario(alvo_id: int, _: int = Depends(get_usuario_logado)):
    return post_service.listar_por_usuario(alvo_id)


@router.get("/posts")
def listar_posts(_: int = Depends(get_usuario_logado)):
    return post_service.listar_todos()


@router.post("/posts")
async def criar_post(
    conteudo: str = Form(...),
    imagem: Optional[UploadFile] = File(None),
    usuario_id: int = Depends(get_usuario_logado),
):
    imagem_bytes = None
    imagem_ext = None
    if imagem and imagem.filename:
        imagem_ext = os.path.splitext(imagem.filename)[1].lower()
        imagem_bytes = await imagem.read()

    return post_service.criar(usuario_id, conteudo, imagem_bytes, imagem_ext)


@router.delete("/posts/{id_post}")
def deletar_post(id_post: int, usuario_id: int = Depends(get_usuario_logado)):
    return post_service.deletar(id_post, usuario_id)
