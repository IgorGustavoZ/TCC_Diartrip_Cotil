from fastapi import HTTPException
from database import get_db
from utils.cloudinary_upload import upload_imagem, deletar_imagem
from utils.imagem_utils import validar_imagem, strip_exif

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
        # Validação robusta usando magic bytes
        ext = imagem_ext.lstrip(".")
        validar_imagem(imagem_bytes, ext, MAX_IMAGE_SIZE)
        imagem_bytes = strip_exif(imagem_bytes, ext)
        imagem_url = upload_imagem(imagem_bytes, "diartrip/posts")

    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "INSERT INTO posts (id_usuario, conteudo, imagem) VALUES (%s, %s, %s)",
                (usuario_id, conteudo.strip(), imagem_url),
            )
            conexao.commit()
            return {"mensagem": "Post criado", "id_post": cursor.lastrowid}
        except Exception:
            if imagem_url:
                deletar_imagem(imagem_url)
            raise
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
                deletar_imagem(post[1])

            return {"mensagem": "Post removido"}
        finally:
            cursor.close()
