from fastapi import HTTPException
from database import get_db
from utils.cloudinary_upload import upload_imagem, deletar_imagem
from utils.imagem_utils import validar_imagem, strip_exif

MAX_IMAGE_SIZE = 10 * 1024 * 1024


def listar_todos(usuario_id: int, limite: int = 50, offset: int = 0) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT p.id_post, p.conteudo, p.imagem,
                       COALESCE(p.data_criacao, NOW()) AS data_criacao,
                       u.id_usuario, u.nome, u.foto_perfil,
                       COUNT(DISTINCT pc.id) AS curtidas,
                       COALESCE(MAX(CASE WHEN pc.id_usuario = %s THEN 1 ELSE 0 END), 0) AS ja_curtiu
                FROM posts p
                JOIN usuarios u ON p.id_usuario = u.id_usuario
                LEFT JOIN post_curtidas pc ON pc.id_post = p.id_post
                GROUP BY p.id_post, p.conteudo, p.imagem, p.data_criacao,
                         u.id_usuario, u.nome, u.foto_perfil
                ORDER BY p.data_criacao DESC
                LIMIT %s OFFSET %s
                """,
                (usuario_id, limite, offset),
            )
            posts = cursor.fetchall()
            if not posts:
                return []

            ids = [p["id_post"] for p in posts]
            fmt = ",".join(["%s"] * len(ids))
            cursor.execute(
                f"""
                SELECT c.id, c.id_post, c.id_usuario, c.conteudo,
                       COALESCE(c.data_criacao, NOW()) AS data_criacao,
                       u.nome, u.foto_perfil
                FROM post_comentarios c
                JOIN usuarios u ON c.id_usuario = u.id_usuario
                WHERE c.id_post IN ({fmt})
                ORDER BY c.data_criacao ASC
                """,
                ids,
            )
            coments_map: dict = {}
            for c in cursor.fetchall():
                coments_map.setdefault(c["id_post"], []).append(c)

            for p in posts:
                p["comentarios"] = coments_map.get(p["id_post"], [])

            return posts
        finally:
            cursor.close()


def listar_por_usuario(alvo_id: int, usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT p.id_post, p.conteudo, p.imagem,
                       COALESCE(p.data_criacao, NOW()) AS data_criacao,
                       u.id_usuario, u.nome, u.foto_perfil,
                       COUNT(DISTINCT pc.id) AS curtidas,
                       COALESCE(MAX(CASE WHEN pc.id_usuario = %s THEN 1 ELSE 0 END), 0) AS ja_curtiu
                FROM posts p
                JOIN usuarios u ON p.id_usuario = u.id_usuario
                LEFT JOIN post_curtidas pc ON pc.id_post = p.id_post
                WHERE p.id_usuario = %s
                GROUP BY p.id_post, p.conteudo, p.imagem, p.data_criacao,
                         u.id_usuario, u.nome, u.foto_perfil
                ORDER BY p.data_criacao DESC
                LIMIT 20
                """,
                (usuario_id, alvo_id),
            )
            posts = cursor.fetchall()
            if not posts:
                return []

            ids = [p["id_post"] for p in posts]
            fmt = ",".join(["%s"] * len(ids))
            cursor.execute(
                f"""
                SELECT c.id, c.id_post, c.id_usuario, c.conteudo,
                       COALESCE(c.data_criacao, NOW()) AS data_criacao,
                       u.nome, u.foto_perfil
                FROM post_comentarios c
                JOIN usuarios u ON c.id_usuario = u.id_usuario
                WHERE c.id_post IN ({fmt})
                ORDER BY c.data_criacao ASC
                """,
                ids,
            )
            coments_map: dict = {}
            for c in cursor.fetchall():
                coments_map.setdefault(c["id_post"], []).append(c)

            for p in posts:
                p["comentarios"] = coments_map.get(p["id_post"], [])

            return posts
        finally:
            cursor.close()


def criar(usuario_id: int, conteudo: str, imagem_bytes: bytes | None, imagem_ext: str | None) -> dict:
    if not conteudo.strip() and imagem_bytes is None:
        raise HTTPException(status_code=400, detail="O post deve ter texto ou imagem")

    imagem_url = None
    if imagem_bytes is not None:
        ext = (imagem_ext or "").lstrip(".").lower()
        if not ext:
            if imagem_bytes.startswith(b"\xff\xd8"): ext = "jpg"
            elif imagem_bytes.startswith(b"\x89PNG"): ext = "png"
            elif b"WEBP" in imagem_bytes[:16]: ext = "webp"
            else: ext = "jpg"
            from utils.logger import get_logger
            get_logger("post_service").info("Extensão de post inferida: %s", ext)

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


def curtir(id_post: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute("SELECT 1 FROM posts WHERE id_post=%s", (id_post,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Post não encontrado")

            cursor.execute(
                "SELECT id FROM post_curtidas WHERE id_post=%s AND id_usuario=%s",
                (id_post, usuario_id),
            )
            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    "DELETE FROM post_curtidas WHERE id_post=%s AND id_usuario=%s",
                    (id_post, usuario_id),
                )
                curtiu = False
            else:
                cursor.execute(
                    "INSERT INTO post_curtidas (id_post, id_usuario) VALUES (%s, %s)",
                    (id_post, usuario_id),
                )
                curtiu = True

            cursor.execute(
                "SELECT COUNT(*) AS total FROM post_curtidas WHERE id_post=%s",
                (id_post,),
            )
            total = cursor.fetchone()["total"]

            return {"curtiu": curtiu, "total_curtidas": total}
        finally:
            cursor.close()


def comentar(id_post: int, usuario_id: int, conteudo: str) -> dict:
    conteudo = conteudo.strip()
    if not conteudo:
        raise HTTPException(status_code=400, detail="Comentário vazio")
    if len(conteudo) > 1000:
        raise HTTPException(status_code=400, detail="Comentário muito longo. Máximo 1000 caracteres.")

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute("SELECT 1 FROM posts WHERE id_post=%s", (id_post,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Post não encontrado")

            cursor.execute(
                "INSERT INTO post_comentarios (id_post, id_usuario, conteudo) VALUES (%s, %s, %s)",
                (id_post, usuario_id, conteudo),
            )
            id_comentario = cursor.lastrowid

            cursor.execute(
                """
                SELECT c.id, c.id_post, c.id_usuario, c.conteudo,
                       COALESCE(c.data_criacao, NOW()) AS data_criacao,
                       u.nome, u.foto_perfil
                FROM post_comentarios c
                JOIN usuarios u ON c.id_usuario = u.id_usuario
                WHERE c.id = %s
                """,
                (id_comentario,),
            )
            return cursor.fetchone()
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
