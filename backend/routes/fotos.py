import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import Optional
from schemas import FotoResponse, FotoCriada, MensagemResponse
from utils.auth import get_usuario_logado
from utils.rate_limiter import verificar_rate_limit
from services import foto_service

router = APIRouter()


_MAX_FOTO_BYTES = 5 * 1024 * 1024


@router.get("/grupos/{id_grupo}/fotos", response_model=list[FotoResponse])
def listar_fotos(
    id_grupo: int,
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    usuario_id: int = Depends(get_usuario_logado),
):
    return foto_service.listar(id_grupo, usuario_id, limite, offset)


@router.post("/grupos/{id_grupo}/fotos", response_model=FotoCriada, status_code=201)
def upload_foto(
    id_grupo: int,
    arquivo: UploadFile = File(...),
    template_usado: Optional[str] = Form(None),
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"upload_foto:{usuario_id}", limite=20)
    arquivo.file.seek(0, os.SEEK_END)
    tamanho = arquivo.file.tell()
    print(f"[UPLOAD_FOTO] filename={arquivo.filename!r} content_type={arquivo.content_type!r} size={tamanho}")
    if tamanho > _MAX_FOTO_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Máximo 5 MB.")
    arquivo.file.seek(0)
    conteudo = arquivo.file.read()
    arquivo.file.close()

    return foto_service.salvar(
        id_grupo=id_grupo,
        usuario_id=usuario_id,
        arquivo_nome=arquivo.filename or "",
        arquivo_bytes=conteudo,
        arquivo_size=tamanho,
        template_usado=template_usado,
    )


@router.delete("/fotos/{id_foto}", response_model=MensagemResponse)
def deletar_foto(id_foto: int, usuario_id: int = Depends(get_usuario_logado)):
    return foto_service.deletar(id_foto, usuario_id)
