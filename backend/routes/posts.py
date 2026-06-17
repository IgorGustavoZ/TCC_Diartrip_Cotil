import os
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional
from schemas import PostResponse, PostCriado, CurtirResponse, ComentarioResponse, MensagemResponse
from utils.auth import get_usuario_logado
from utils.rate_limiter import verificar_rate_limit
from services import post_service

router = APIRouter()

_MAX_POST_FOTO_BYTES = 10 * 1024 * 1024


@router.get("/posts/usuario/{alvo_id}", response_model=list[PostResponse])
def posts_do_usuario(alvo_id: int, usuario_id: int = Depends(get_usuario_logado)):
    return post_service.listar_por_usuario(alvo_id, usuario_id)


@router.get("/posts", response_model=list[PostResponse])
def listar_posts(
    limite: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    usuario_id: int = Depends(get_usuario_logado),
):
    return post_service.listar_todos(usuario_id, limite, offset)


@router.post("/posts", response_model=PostCriado, status_code=201)
async def criar_post(
    conteudo: str = Form(..., max_length=5000),
    imagem: Optional[UploadFile] = File(None),
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"criar_post:{usuario_id}", limite=20)
    imagem_bytes = None
    imagem_ext = None
    if imagem and imagem.filename:
        imagem_ext = os.path.splitext(imagem.filename)[1].lower()
        imagem_bytes = await imagem.read(_MAX_POST_FOTO_BYTES + 1)
        print(f"[POST_IMAGEM] filename={imagem.filename!r} content_type={imagem.content_type!r} ext={imagem_ext!r} size={len(imagem_bytes)}")
        if len(imagem_bytes) > _MAX_POST_FOTO_BYTES:
            raise HTTPException(status_code=413, detail="Imagem muito grande. Máximo 10 MB.")

    return post_service.criar(usuario_id, conteudo, imagem_bytes, imagem_ext)


@router.post("/posts/{id_post}/curtir", response_model=CurtirResponse)
def curtir_post(id_post: int, usuario_id: int = Depends(get_usuario_logado)):
    verificar_rate_limit(f"curtir:{usuario_id}", limite=60)
    return post_service.curtir(id_post, usuario_id)


class ComentarioInput(BaseModel):
    conteudo: str = Field(..., min_length=1, max_length=1000)


@router.post("/posts/{id_post}/comentar", response_model=ComentarioResponse)
def comentar_post(
    id_post: int,
    dados: ComentarioInput,
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"comentar:{usuario_id}", limite=20)
    return post_service.comentar(id_post, usuario_id, dados.conteudo)


@router.delete("/posts/{id_post}", response_model=MensagemResponse)
def deletar_post(id_post: int, usuario_id: int = Depends(get_usuario_logado)):
    return post_service.deletar(id_post, usuario_id)
