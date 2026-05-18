from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo


def listar(id_grupo: int, usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                """
                SELECT u.id_usuario, u.nome, gm.cargo
                FROM grupo_membros gm
                JOIN usuarios u ON gm.id_usuario = u.id_usuario
                WHERE gm.id_grupo = %s
                """,
                (id_grupo,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def adicionar(id_grupo: int, id_usuario_novo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)
            if cargo != "admin":
                raise HTTPException(status_code=403, detail="Apenas admin pode adicionar membros")

            cursor.execute(
                "SELECT 1 FROM usuarios WHERE id_usuario=%s", (id_usuario_novo,)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            cursor.execute(
                "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, id_usuario_novo),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Usuário já está no grupo")

            cursor2 = conexao.cursor()
            cursor2.execute(
                "INSERT INTO grupo_membros (id_grupo, id_usuario) VALUES (%s, %s)",
                (id_grupo, id_usuario_novo),
            )
            conexao.commit()
            cursor2.close()
            return {"mensagem": "Membro adicionado"}
        finally:
            cursor.close()


def _checar_ultimo_admin(cursor, id_grupo: int, id_alvo: int) -> None:
    """Impede remover/rebaixar o último admin se ainda há outros membros."""
    cursor.execute(
        "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
        (id_grupo, id_alvo),
    )
    alvo = cursor.fetchone()
    if alvo and alvo["cargo"] == "admin":
        cursor.execute(
            "SELECT COUNT(*) as qtd FROM grupo_membros WHERE id_grupo=%s AND cargo='admin'",
            (id_grupo,),
        )
        if cursor.fetchone()["qtd"] <= 1:
            cursor.execute(
                "SELECT COUNT(*) as qtd FROM grupo_membros WHERE id_grupo=%s", (id_grupo,)
            )
            if cursor.fetchone()["qtd"] > 1:
                raise HTTPException(
                    status_code=400,
                    detail="Promova outro membro a admin antes de remover o último admin",
                )


def remover(id_grupo: int, id_usuario_remover: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo_atual = checar_membro_grupo(cursor, id_grupo, usuario_id)
            if usuario_id != id_usuario_remover and cargo_atual != "admin":
                raise HTTPException(status_code=403, detail="Sem permissão")

            _checar_ultimo_admin(cursor, id_grupo, id_usuario_remover)

            cursor2 = conexao.cursor()
            cursor2.execute(
                "DELETE FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, id_usuario_remover),
            )
            conexao.commit()
            if cursor2.rowcount == 0:
                raise HTTPException(status_code=404, detail="Membro não encontrado")
            cursor2.close()
            return {"mensagem": "Membro removido"}
        finally:
            cursor.close()


def promover(id_grupo: int, id_usuario_promover: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)
            if cargo != "admin":
                raise HTTPException(status_code=403, detail="Apenas admin pode promover")

            cursor2 = conexao.cursor()
            cursor2.execute(
                "UPDATE grupo_membros SET cargo='admin' WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, id_usuario_promover),
            )
            conexao.commit()
            if cursor2.rowcount == 0:
                raise HTTPException(status_code=404, detail="Membro não encontrado ou já é admin")
            cursor2.close()
            return {"mensagem": "Usuário promovido a admin"}
        finally:
            cursor.close()


def rebaixar(id_grupo: int, id_usuario_rebaixar: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)
            if cargo != "admin":
                raise HTTPException(status_code=403, detail="Apenas admins podem rebaixar membros")

            _checar_ultimo_admin(cursor, id_grupo, id_usuario_rebaixar)

            cursor2 = conexao.cursor()
            cursor2.execute(
                "UPDATE grupo_membros SET cargo='membro' WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, id_usuario_rebaixar),
            )
            conexao.commit()
            if cursor2.rowcount == 0:
                raise HTTPException(
                    status_code=404, detail="Membro não encontrado ou já é membro comum"
                )
            cursor2.close()
            return {"mensagem": "Usuário rebaixado para membro comum"}
        finally:
            cursor.close()


def sair(id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            _checar_ultimo_admin(cursor, id_grupo, usuario_id)

            cursor2 = conexao.cursor()
            cursor2.execute(
                "DELETE FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, usuario_id),
            )
            conexao.commit()
            if cursor2.rowcount == 0:
                raise HTTPException(status_code=404, detail="Você não está no grupo")
            cursor2.close()
            return {"mensagem": "Saiu do grupo"}
        finally:
            cursor.close()
