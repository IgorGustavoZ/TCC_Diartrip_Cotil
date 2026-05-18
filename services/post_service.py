import os
import uuid
from fastapi import HTTPException
from database import get_db

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024


def listar_todos() -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT p.id_post, p.conteudo, p.imagem, p.data_criacao,
                       u.id_usuario, u.nome, u.foto_perfil
                FROM posts p
                JOIN usuarios u ON p.id_usuario = u.id_usuario
                ORDER BY p.data_criacao DESC
                LIMIT 100
                """
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def listar_por_usuario(alvo_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT p.id_post, p.conteudo, p.imagem, p.data_criacao,
                       u.id_usuario, u.nome, u.foto_perfil
                FROM posts p
                JOIN usuarios u ON p.id_usuario = u.id_usuario
                WHERE p.id_usuario = %s
                ORDER BY p.data_criacao DESC
                LIMIT 20
                """,
                (alvo_id,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def criar(usuario_id: int, conteudo: str, imagem_bytes: bytes | None, imagem_ext: str | None) -> dict:
    if not conteudo.strip():
        raise HTTPException(status_code=400, detail="Conteúdo vazio")

    imagem_url = None
    if imagem_bytes is not None and imagem_ext is not None:
        if imagem_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail="Formato inválido. Use JPG, PNG ou WebP.")
        if len(imagem_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=422, detail="Imagem muito grande. Máximo 10 MB.")
        nome = f"post_{uuid.uuid4().hex}{imagem_ext}"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(os.path.join(UPLOAD_DIR, nome), "wb") as f:
            f.write(imagem_bytes)
        imagem_url = f"/uploads/{nome}"

    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "INSERT INTO posts (id_usuario, conteudo, imagem) VALUES (%s, %s, %s)",
                (usuario_id, conteudo.strip(), imagem_url),
            )
            conexao.commit()
            return {"mensagem": "Post criado", "id_post": cursor.lastrowid}
        finally:
            cursor.close()


def deletar(id_post: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT id_usuario, imagem FROM posts WHERE id_post=%s", (id_post,))
            post = cursor.fetchone()
            if not post:
                raise HTTPException(status_code=404, detail="Post não encontrado")
            if post[0] != usuario_id:
                raise HTTPException(status_code=403, detail="Sem permissão")

            cursor.execute("DELETE FROM posts WHERE id_post=%s", (id_post,))
            conexao.commit()

            if post[1]:
                caminho = os.path.join(UPLOAD_DIR, os.path.basename(post[1]))
                try:
                    if os.path.exists(caminho):
                        os.remove(caminho)
                except OSError:
                    pass

            return {"mensagem": "Post removido"}
        finally:
            cursor.close()
