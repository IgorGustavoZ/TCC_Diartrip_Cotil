"""Comunidades — grupos temáticos (ex.: "Amantes do Japão"). NÃO são viagens:
sem datas, sem roteiro, sem orçamento. Reaproveitam só o MOLDE de
grupos_viagem/grupo_membros (cargo admin/membro), como entidade própria —
mesmo padrão de tabelas, mas tabelas próprias, porque conceitualmente são
coisas diferentes (ver alembic/versions/008_explorar_social.py).
"""
import secrets
import string

from fastapi import HTTPException
from mysql.connector import IntegrityError

from database import get_db
from utils.cloudinary_upload import upload_imagem, deletar_imagem
from utils.imagem_utils import validar_imagem, strip_exif


def _gerar_codigo() -> str:
    """Mesma ideia do código de convite de grupos_viagem
    (grupo_service._gerar_codigo): 6 caracteres, gerados com secrets.choice."""
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(6))


def _checar_admin(cursor, id_comunidade: int, usuario_id: int) -> None:
    cursor.execute(
        "SELECT cargo FROM comunidade_membros WHERE id_comunidade=%s AND id_usuario=%s",
        (id_comunidade, usuario_id),
    )
    membro = cursor.fetchone()
    if not membro:
        raise HTTPException(status_code=403, detail="Você não pertence a esta comunidade")
    if membro["cargo"] != "admin":
        raise HTTPException(
            status_code=403, detail="Apenas administradores podem realizar esta ação"
        )


def criar(usuario_id: int, nome: str, descricao: str | None, categoria: str | None, privacidade: str) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            # Código gerado sempre (mesmo pra pública): se o admin trocar a
            # privacidade pra privada depois, o código já existe.
            for _ in range(5):
                codigo_convite = _gerar_codigo()
                try:
                    cursor.execute(
                        "INSERT INTO comunidades (nome, descricao, categoria, privacidade, "
                        "codigo_convite, criado_por) VALUES (%s, %s, %s, %s, %s, %s)",
                        (
                            nome.strip(),
                            (descricao or "").strip() or None,
                            (categoria or "").strip() or None,
                            privacidade,
                            codigo_convite,
                            usuario_id,
                        ),
                    )
                    break
                except IntegrityError as e:
                    if e.errno == 1062:
                        conexao.rollback()
                        continue
                    raise
            else:
                raise HTTPException(status_code=500, detail="Não foi possível gerar um código de convite único")

            id_comunidade = cursor.lastrowid
            # Quem cria vira admin da própria comunidade, igual ao criador
            # de uma viagem em grupo_service.criar().
            cursor.execute(
                "INSERT INTO comunidade_membros (id_comunidade, id_usuario, cargo) VALUES (%s, %s, 'admin')",
                (id_comunidade, usuario_id),
            )
            return {"mensagem": "Comunidade criada", "id_comunidade": id_comunidade}
        finally:
            cursor.close()


def listar(usuario_id: int, busca: str | None, limite: int = 20, offset: int = 0) -> list:
    """Comunidades públicas + as privadas das quais o usuário já é membro —
    uma comunidade privada nunca aparece pra quem não faz parte dela."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            sql = """
                SELECT c.id_comunidade, c.nome, c.descricao, c.foto_capa, c.categoria, c.privacidade,
                       c.criado_por, u.nome AS criador,
                       (SELECT COUNT(*) FROM comunidade_membros cm
                        WHERE cm.id_comunidade = c.id_comunidade) AS total_membros,
                       (SELECT 1 FROM comunidade_membros cm2
                        WHERE cm2.id_comunidade = c.id_comunidade AND cm2.id_usuario = %s) AS sou_membro
                FROM comunidades c
                JOIN usuarios u ON u.id_usuario = c.criado_por
                WHERE (
                    c.privacidade = 'publica'
                    OR c.id_comunidade IN (SELECT id_comunidade FROM comunidade_membros WHERE id_usuario = %s)
                )
            """
            params: list = [usuario_id, usuario_id]
            if busca:
                busca_safe = busca.strip()
                sql += " AND (c.nome LIKE %s OR c.categoria LIKE %s)"
                params.extend([f"%{busca_safe}%", f"%{busca_safe}%"])
            sql += " ORDER BY total_membros DESC, c.data_criacao DESC LIMIT %s OFFSET %s"
            params.extend([limite, offset])
            cursor.execute(sql, tuple(params))
            comunidades = cursor.fetchall()
            for c in comunidades:
                c["sou_membro"] = bool(c["sou_membro"])
            return comunidades
        finally:
            cursor.close()


def detalhar(id_comunidade: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT c.id_comunidade, c.nome, c.descricao, c.foto_capa, c.categoria, c.privacidade,
                       c.criado_por, u.nome AS criador,
                       (SELECT COUNT(*) FROM comunidade_membros cm
                        WHERE cm.id_comunidade = c.id_comunidade) AS total_membros
                FROM comunidades c JOIN usuarios u ON u.id_usuario = c.criado_por
                WHERE c.id_comunidade=%s
                """,
                (id_comunidade,),
            )
            comunidade = cursor.fetchone()
            if not comunidade:
                raise HTTPException(status_code=404, detail="Comunidade não encontrada")

            cursor.execute(
                "SELECT cargo FROM comunidade_membros WHERE id_comunidade=%s AND id_usuario=%s",
                (id_comunidade, usuario_id),
            )
            membro = cursor.fetchone()
            if comunidade["privacidade"] == "privada" and not membro:
                raise HTTPException(status_code=403, detail="Esta comunidade é privada")

            comunidade["sou_membro"] = membro is not None
            comunidade["meu_cargo"] = membro["cargo"] if membro else None
            return comunidade
        finally:
            cursor.close()


def atualizar(
    id_comunidade: int, usuario_id: int, nome: str, descricao: str | None,
    categoria: str | None, privacidade: str,
) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            _checar_admin(cursor, id_comunidade, usuario_id)
            cursor.execute(
                "UPDATE comunidades SET nome=%s, descricao=%s, categoria=%s, privacidade=%s "
                "WHERE id_comunidade=%s",
                (
                    nome.strip(),
                    (descricao or "").strip() or None,
                    (categoria or "").strip() or None,
                    privacidade,
                    id_comunidade,
                ),
            )
            return {"mensagem": "Comunidade atualizada"}
        finally:
            cursor.close()


def obter_codigo_convite(id_comunidade: int, usuario_id: int) -> dict:
    """Código de convite só existe pra quem acessa (faz sentido): se a
    comunidade for pública, qualquer um entra direto, sem código — então o
    código nem deve ser exposto nesse caso."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            _checar_admin(cursor, id_comunidade, usuario_id)
            cursor.execute(
                "SELECT codigo_convite, privacidade FROM comunidades WHERE id_comunidade=%s",
                (id_comunidade,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Comunidade não encontrada")
            if row["privacidade"] != "privada":
                raise HTTPException(
                    status_code=400,
                    detail="Código de convite só existe para comunidades privadas",
                )
            return {"codigo_convite": row["codigo_convite"]}
        finally:
            cursor.close()


def atualizar_foto(id_comunidade: int, usuario_id: int, arquivo_nome: str, arquivo_bytes: bytes) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            _checar_admin(cursor, id_comunidade, usuario_id)
        finally:
            cursor.close()

    ext = arquivo_nome.rsplit(".", 1)[-1].lower() if "." in arquivo_nome else ""
    if not ext:
        if arquivo_bytes.startswith(b"\xff\xd8"): ext = "jpg"
        elif arquivo_bytes.startswith(b"\x89PNG"): ext = "png"
        elif b"WEBP" in arquivo_bytes[:16]: ext = "webp"
        else: ext = "jpg"

    validar_imagem(arquivo_bytes, ext)
    arquivo_bytes = strip_exif(arquivo_bytes, ext)
    foto_url = upload_imagem(arquivo_bytes, "diartrip/comunidades", public_id=f"comunidade_{id_comunidade}")

    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "UPDATE comunidades SET foto_capa=%s WHERE id_comunidade=%s",
                (foto_url, id_comunidade),
            )
            return {"foto_capa": foto_url}
        finally:
            cursor.close()


def excluir(id_comunidade: int, usuario_id: int) -> dict:
    """Só o admin (= quem criou, já que comunidades não têm promoção de
    cargo — ver criar()) pode excluir. Reaproveita _checar_admin, a mesma
    checagem já usada em atualizar()/obter_codigo_convite()/atualizar_foto().
    Apaga os registros dependentes explicitamente antes da comunidade — mesmo
    padrão de grupo_service.deletar() — e só então limpa as imagens no
    Cloudinary (capa + fotos dos posts), depois do commit da exclusão."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            _checar_admin(cursor, id_comunidade, usuario_id)

            cursor.execute(
                "SELECT foto_capa FROM comunidades WHERE id_comunidade=%s", (id_comunidade,)
            )
            row = cursor.fetchone()
            foto_capa = row["foto_capa"] if row else None

            cursor.execute(
                "SELECT imagem FROM posts WHERE id_comunidade=%s AND imagem IS NOT NULL",
                (id_comunidade,),
            )
            imagens_posts = [r["imagem"] for r in cursor.fetchall()]

            cursor.execute("DELETE FROM posts WHERE id_comunidade=%s", (id_comunidade,))
            cursor.execute("DELETE FROM comunidade_membros WHERE id_comunidade=%s", (id_comunidade,))
            cursor.execute("DELETE FROM comunidades WHERE id_comunidade=%s", (id_comunidade,))

            for url in ([foto_capa] if foto_capa else []) + imagens_posts:
                deletar_imagem(url)

            return {"mensagem": "Comunidade excluída"}
        finally:
            cursor.close()


def entrar(id_comunidade: int, usuario_id: int, codigo: str | None = None) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT privacidade, codigo_convite FROM comunidades WHERE id_comunidade=%s",
                (id_comunidade,),
            )
            comunidade = cursor.fetchone()
            if not comunidade:
                raise HTTPException(status_code=404, detail="Comunidade não encontrada")

            if comunidade["privacidade"] == "privada":
                codigo_informado = (codigo or "").strip().upper()
                if not codigo_informado or codigo_informado != comunidade["codigo_convite"]:
                    raise HTTPException(
                        status_code=403,
                        detail="Código de convite inválido para esta comunidade privada",
                    )

            cursor.execute(
                "SELECT 1 FROM comunidade_membros WHERE id_comunidade=%s AND id_usuario=%s",
                (id_comunidade, usuario_id),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Você já é membro desta comunidade")

            cursor.execute(
                "INSERT INTO comunidade_membros (id_comunidade, id_usuario) VALUES (%s, %s)",
                (id_comunidade, usuario_id),
            )
            return {"mensagem": "Você entrou na comunidade"}
        finally:
            cursor.close()


def sair(id_comunidade: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT criado_por FROM comunidades WHERE id_comunidade=%s", (id_comunidade,)
            )
            comunidade = cursor.fetchone()
            if not comunidade:
                raise HTTPException(status_code=404, detail="Comunidade não encontrada")
            if comunidade["criado_por"] == usuario_id:
                raise HTTPException(
                    status_code=400, detail="O criador não pode sair da própria comunidade"
                )

            cursor.execute(
                "DELETE FROM comunidade_membros WHERE id_comunidade=%s AND id_usuario=%s",
                (id_comunidade, usuario_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=400, detail="Você não é membro desta comunidade")
            return {"mensagem": "Você saiu da comunidade"}
        finally:
            cursor.close()
