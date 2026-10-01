from fastapi import HTTPException
from database import get_db
from utils.cloudinary_upload import upload_imagem, deletar_imagem
from utils.imagem_utils import validar_imagem, strip_exif
from utils.dependencies import checar_membro_grupo, checar_membro_comunidade

MAX_IMAGE_SIZE = 10 * 1024 * 1024

_TIPOS_VALIDOS = {"texto", "viagem", "roteiro"}

_SELECT_POST = """
    SELECT p.id_post, p.id_grupo, p.id_comunidade, p.tipo, p.conteudo, p.imagem,
           COALESCE(p.data_criacao, NOW()) AS data_criacao,
           u.id_usuario, u.nome, u.foto_perfil,
           COUNT(DISTINCT pc.id) AS curtidas,
           COALESCE(MAX(CASE WHEN pc.id_usuario = %s THEN 1 ELSE 0 END), 0) AS ja_curtiu,
           p.ref_id_grupo, p.ref_id_roteiro
    FROM posts p
    JOIN usuarios u ON p.id_usuario = u.id_usuario
    LEFT JOIN post_curtidas pc ON pc.id_post = p.id_post
"""
_GROUP_BY_POST = """
    GROUP BY p.id_post, p.id_grupo, p.id_comunidade, p.tipo, p.conteudo, p.imagem, p.data_criacao,
             u.id_usuario, u.nome, u.foto_perfil, p.ref_id_grupo, p.ref_id_roteiro
"""


def _anexar_comentarios(cursor, posts: list[dict]) -> None:
    if not posts:
        return
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


def _anexar_referencias(cursor, posts: list[dict]) -> None:
    """Preenche ref_grupo (tipo='viagem') / ref_roteiro (tipo='roteiro') com
    dados ATUAIS, sempre lidos ao vivo — nunca copiados para dentro do post.

    Não existe um ID separado para "o roteiro completo" de uma viagem: o
    conjunto de itens em `roteiros` com aquele id_grupo JÁ É o roteiro
    completo. Por isso tipo='roteiro' também usa ref_id_grupo (mesma coluna
    de tipo='viagem') — o que muda é o que é buscado: para 'viagem', os
    dados da viagem; para 'roteiro', a viagem + TODOS os itens dela."""
    ids_grupo_viagem = {p["ref_id_grupo"] for p in posts if p.get("tipo") == "viagem" and p.get("ref_id_grupo")}
    ids_grupo_roteiro = {p["ref_id_grupo"] for p in posts if p.get("tipo") == "roteiro" and p.get("ref_id_grupo")}

    grupos_map: dict = {}
    if ids_grupo_viagem:
        fmt = ",".join(["%s"] * len(ids_grupo_viagem))
        cursor.execute(
            f"""
            SELECT g.id_grupo, g.nome_grupo, g.destino_principal, g.data_inicio, g.data_fim,
                   g.limite_participantes,
                   (SELECT COUNT(*) FROM grupo_membros gm WHERE gm.id_grupo = g.id_grupo) AS vagas_ocupadas
            FROM grupos_viagem g WHERE g.id_grupo IN ({fmt})
            """,
            list(ids_grupo_viagem),
        )
        grupos_map = {g["id_grupo"]: g for g in cursor.fetchall()}

    roteiros_map: dict = {}
    if ids_grupo_roteiro:
        fmt = ",".join(["%s"] * len(ids_grupo_roteiro))
        cursor.execute(
            f"SELECT id_grupo, nome_grupo, destino_principal FROM grupos_viagem WHERE id_grupo IN ({fmt})",
            list(ids_grupo_roteiro),
        )
        info_grupos = {g["id_grupo"]: g for g in cursor.fetchall()}

        cursor.execute(
            f"""
            SELECT id_grupo, titulo, descricao FROM roteiros
            WHERE id_grupo IN ({fmt}) ORDER BY id_grupo, data_criacao ASC
            """,
            list(ids_grupo_roteiro),
        )
        itens_por_grupo: dict = {}
        for r in cursor.fetchall():
            itens_por_grupo.setdefault(r["id_grupo"], []).append(
                {"titulo": r["titulo"], "descricao": r["descricao"]}
            )

        for id_grupo, info in info_grupos.items():
            itens = itens_por_grupo.get(id_grupo, [])
            roteiros_map[id_grupo] = {
                "id_grupo": id_grupo,
                "nome_grupo": info["nome_grupo"],
                "destino_principal": info["destino_principal"],
                "total_itens": len(itens),
                "itens": itens,
            }

    for p in posts:
        if p.get("tipo") == "viagem":
            p["ref_grupo"] = grupos_map.get(p.get("ref_id_grupo"))
            p["ref_roteiro"] = None
        elif p.get("tipo") == "roteiro":
            p["ref_grupo"] = None
            p["ref_roteiro"] = roteiros_map.get(p.get("ref_id_grupo"))
        else:
            p["ref_grupo"] = None
            p["ref_roteiro"] = None


def listar_todos(usuario_id: int, limite: int = 50, offset: int = 0) -> list:
    """O Feed global — só posts sem grupo/comunidade (publicações de
    verdade: texto, ou viagem/roteiro que alguém decidiu compartilhar). O
    mini feed de cada viagem e o feed de cada comunidade são privados aos
    seus membros e só aparecem em listar_por_grupo()/listar_por_comunidade()."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                _SELECT_POST + " WHERE p.id_grupo IS NULL AND p.id_comunidade IS NULL"
                + _GROUP_BY_POST + " ORDER BY p.data_criacao DESC LIMIT %s OFFSET %s",
                (usuario_id, limite, offset),
            )
            posts = cursor.fetchall()
            if not posts:
                return []
            _anexar_comentarios(cursor, posts)
            _anexar_referencias(cursor, posts)
            return posts
        finally:
            cursor.close()


def listar_por_usuario(alvo_id: int, usuario_id: int) -> list:
    """Posts do perfil público de alguém — só os do Feed global. Os posts que
    a pessoa fez num mini feed de viagem ou numa comunidade são privados aos
    membros de lá e nunca aparecem aqui, mesmo para quem visita o perfil dela."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                _SELECT_POST
                + " WHERE p.id_usuario = %s AND p.id_grupo IS NULL AND p.id_comunidade IS NULL"
                + _GROUP_BY_POST + " ORDER BY p.data_criacao DESC LIMIT 20",
                (usuario_id, alvo_id),
            )
            posts = cursor.fetchall()
            if not posts:
                return []
            _anexar_comentarios(cursor, posts)
            _anexar_referencias(cursor, posts)
            return posts
        finally:
            cursor.close()


def listar_por_grupo(id_grupo: int, usuario_id: int) -> list:
    """Mini feed privado da viagem — só quem é membro do grupo enxerga."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                _SELECT_POST + " WHERE p.id_grupo = %s" + _GROUP_BY_POST
                + " ORDER BY p.data_criacao DESC",
                (usuario_id, id_grupo),
            )
            posts = cursor.fetchall()
            if not posts:
                return []
            _anexar_comentarios(cursor, posts)
            _anexar_referencias(cursor, posts)
            return posts
        finally:
            cursor.close()


def listar_por_comunidade(id_comunidade: int, usuario_id: int) -> list:
    """Feed privado da comunidade — só quem é membro enxerga."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_comunidade(cursor, id_comunidade, usuario_id)
            cursor.execute(
                _SELECT_POST + " WHERE p.id_comunidade = %s" + _GROUP_BY_POST
                + " ORDER BY p.data_criacao DESC",
                (usuario_id, id_comunidade),
            )
            posts = cursor.fetchall()
            if not posts:
                return []
            _anexar_comentarios(cursor, posts)
            _anexar_referencias(cursor, posts)
            return posts
        finally:
            cursor.close()


def criar(
    usuario_id: int,
    conteudo: str,
    imagem_bytes: bytes | None,
    imagem_ext: str | None,
    id_grupo: int | None = None,
    id_comunidade: int | None = None,
    tipo: str = "texto",
    ref_id_grupo: int | None = None,
    ref_id_roteiro: int | None = None,
) -> dict:
    if id_grupo is not None and id_comunidade is not None:
        raise HTTPException(
            status_code=400,
            detail="Um post não pode pertencer a um grupo e a uma comunidade ao mesmo tempo",
        )
    if tipo not in _TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Tipo de publicação inválido")
    if tipo == "viagem" and not ref_id_grupo:
        raise HTTPException(status_code=400, detail="Informe a viagem que será compartilhada")
    if tipo == "roteiro" and not ref_id_grupo:
        raise HTTPException(status_code=400, detail="Informe a viagem cujo roteiro será compartilhado")
    if tipo == "texto" and not conteudo.strip() and imagem_bytes is None:
        raise HTTPException(status_code=400, detail="O post deve ter texto ou imagem")

    # Toda checagem de permissão acontece ANTES do upload da imagem, pra não
    # subir um arquivo à toa quando a publicação vai ser recusada mesmo.
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            if id_grupo is not None:
                checar_membro_grupo(cursor, id_grupo, usuario_id)
            if id_comunidade is not None:
                checar_membro_comunidade(cursor, id_comunidade, usuario_id)

            if tipo == "viagem":
                cursor.execute(
                    "SELECT publica FROM grupos_viagem WHERE id_grupo=%s", (ref_id_grupo,)
                )
                grupo = cursor.fetchone()
                if not grupo:
                    raise HTTPException(status_code=404, detail="Viagem não encontrada")
                cargo = checar_membro_grupo(cursor, ref_id_grupo, usuario_id)
                if cargo != "admin":
                    raise HTTPException(
                        status_code=403,
                        detail="Apenas administradores podem compartilhar a viagem",
                    )
                if not grupo["publica"]:
                    raise HTTPException(
                        status_code=400,
                        detail="Torne a viagem pública antes de compartilhá-la no Feed",
                    )

            if tipo == "roteiro":
                # O roteiro COMPLETO da viagem é o conjunto de itens com este
                # id_grupo — não há um "id de roteiro" separado para
                # referenciar (ver _anexar_referencias). Não exige a viagem
                # ser pública: o conteúdo já vai embutido na publicação.
                cursor.execute(
                    "SELECT 1 FROM grupos_viagem WHERE id_grupo=%s", (ref_id_grupo,)
                )
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Viagem não encontrada")
                cargo = checar_membro_grupo(cursor, ref_id_grupo, usuario_id)
                if cargo != "admin":
                    raise HTTPException(
                        status_code=403,
                        detail="Apenas administradores podem compartilhar o roteiro",
                    )
                cursor.execute(
                    "SELECT COUNT(*) AS total FROM roteiros WHERE id_grupo=%s", (ref_id_grupo,)
                )
                if cursor.fetchone()["total"] == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Esta viagem ainda não tem nenhum item no roteiro",
                    )
        finally:
            cursor.close()

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
                "INSERT INTO posts (id_usuario, id_grupo, id_comunidade, tipo, ref_id_grupo, "
                "ref_id_roteiro, conteudo, imagem) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    usuario_id, id_grupo, id_comunidade, tipo, ref_id_grupo, ref_id_roteiro,
                    conteudo.strip(), imagem_url,
                ),
            )
            conexao.commit()
            return {"mensagem": "Post criado", "id_post": cursor.lastrowid}
        except Exception:
            if imagem_url:
                deletar_imagem(imagem_url)
            raise
        finally:
            cursor.close()


def _checar_acesso_post(cursor, id_post: int, usuario_id: int) -> None:
    """Post do Feed global (sem grupo/comunidade): qualquer usuário logado
    acessa. Post de mini feed de viagem ou de comunidade: só membros de lá."""
    cursor.execute("SELECT id_grupo, id_comunidade FROM posts WHERE id_post=%s", (id_post,))
    post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    if post["id_grupo"] is not None:
        checar_membro_grupo(cursor, post["id_grupo"], usuario_id)
    elif post["id_comunidade"] is not None:
        checar_membro_comunidade(cursor, post["id_comunidade"], usuario_id)


def curtir(id_post: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            _checar_acesso_post(cursor, id_post, usuario_id)

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
            _checar_acesso_post(cursor, id_post, usuario_id)

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
