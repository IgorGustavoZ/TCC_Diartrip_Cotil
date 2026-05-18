from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
from database import get_db
from utils.auth import get_usuario_logado
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_SIZE = 5 * 1024 * 1024

@router.get("/grupos/{id_grupo}/fotos")
def listar_fotos(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=403, detail="Acesso negado")
        cursor.execute("""
            SELECT f.id_foto, f.caminho_arquivo, f.template_usado, f.data_upload, u.nome
            FROM fotos f
            JOIN usuarios u ON f.id_usuario = u.id_usuario
            WHERE f.id_grupo = %s
            ORDER BY f.data_upload DESC
        """, (id_grupo,))
        fotos = cursor.fetchall()
        cursor.close()
        return fotos

@router.post("/grupos/{id_grupo}/fotos")
def upload_foto(
    id_grupo: int,
    arquivo: UploadFile = File(...),
    template_usado: Optional[str] = Form(None),
    usuario_id: int = Depends(get_usuario_logado)
):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=403, detail="Acesso negado")

        ext = arquivo.filename.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Formato não permitido")

        conteudo = arquivo.file.read()
        if len(conteudo) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="Arquivo muito grande")

        nome_arquivo = f"{uuid.uuid4()}.{ext}"
        caminho = os.path.join(UPLOAD_DIR, nome_arquivo)

        with open(caminho, "wb") as buffer:
            buffer.write(conteudo)
        arquivo.file.close()

        caminho_db = f"/uploads/{nome_arquivo}"
        cursor.execute("""
            INSERT INTO fotos (id_grupo, id_usuario, caminho_arquivo, template_usado)
            VALUES (%s, %s, %s, %s)
        """, (id_grupo, usuario_id, caminho_db, template_usado))
        conexao.commit()
        cursor.close()
        return {"mensagem": "Upload realizado", "url": caminho_db, "id_grupo": id_grupo}

@router.delete("/fotos/{id_foto}")
def deletar_foto(id_foto: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id_usuario, id_grupo, caminho_arquivo FROM fotos WHERE id_foto=%s",
            (id_foto,)
        )
        foto = cursor.fetchone()
        if not foto:
            raise HTTPException(status_code=404, detail="Foto não encontrada")
        dono_id, id_grupo, caminho = foto
        cursor.execute(
            "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        membro = cursor.fetchone()
        if not membro:
            raise HTTPException(status_code=403, detail="Acesso negado")
        if usuario_id != dono_id and membro[0] != "admin":
            raise HTTPException(status_code=403, detail="Sem permissão")
        caminho_fisico = os.path.join(UPLOAD_DIR, os.path.basename(caminho))
        try:
            if os.path.exists(caminho_fisico):
                os.remove(caminho_fisico)
        except OSError as e:
            print(f"Falha ao remover arquivo {caminho_fisico}: {e}")
        cursor.execute("DELETE FROM fotos WHERE id_foto=%s", (id_foto,))
        conexao.commit()
        cursor.close()
        return {"mensagem": "Foto removida"}