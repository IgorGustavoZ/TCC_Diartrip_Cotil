"""Comunidades — grupos temáticos (ex.: "Amantes do Japão"). NÃO são viagens:
sem datas, sem roteiro, sem orçamento. Reaproveitam só o MOLDE de
grupos_viagem/grupo_membros (cargo admin/membro), como entidade própria —
mesmo padrão de tabelas, mas tabelas próprias, porque conceitualmente são
coisas diferentes (ver alembic/versions/008_explorar_social.py).
"""
from fastapi import HTTPException
from database import get_db


def criar(usuario_id: int, nome: str, descricao: str | None, categoria: str | None, privacidade: str) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "INSERT INTO comunidades (nome, descricao, categoria, privacidade, criado_por) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    nome.strip(),
                    (descricao or "").strip() or None,
                    (categoria or "").strip() or None,
                    privacidade,
                    usuario_id,
                ),
            )
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
                SELECT c.id_comunidade, c.nome, c.descricao, c.categoria, c.privacidade,
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
                SELECT c.id_comunidade, c.nome, c.descricao, c.categoria, c.privacidade,
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


def entrar(id_comunidade: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT privacidade FROM comunidades WHERE id_comunidade=%s", (id_comunidade,)
            )
            comunidade = cursor.fetchone()
            if not comunidade:
                raise HTTPException(status_code=404, detail="Comunidade não encontrada")
            # V1: sem convite/aprovação — comunidade privada só aceita quem
            # um admin adicionar diretamente (funcionalidade futura). Fica
            # de fora da busca pública e recusa entrada espontânea.
            if comunidade["privacidade"] == "privada":
                raise HTTPException(
                    status_code=403,
                    detail="Esta comunidade é privada. Peça para um administrador te adicionar.",
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
