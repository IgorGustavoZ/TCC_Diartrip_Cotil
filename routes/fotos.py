import os
from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional
from utils.auth import get_usuario_logado
from services import foto_service

router = APIRouter()


@router.get("/grupos/{id_grupo}/fotos")
def listar_fotos(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return foto_service.listar(id_grupo, usuario_id)


@router.post("/grupos/{id_grupo}/fotos")
def upload_foto(
    id_grupo: int,
    arquivo: UploadFile = File(...),
    template_usado: Optional[str] = Form(None),
    usuario_id: int = Depends(get_usuario_logado),
):
    arquivo.file.seek(0, os.SEEK_END)
    tamanho = arquivo.file.tell()
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


@router.delete("/fotos/{id_foto}")
def deletar_foto(id_foto: int, usuario_id: int = Depends(get_usuario_logado)):
    return foto_service.deletar(id_foto, usuario_id)
