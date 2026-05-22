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

            cursor.execute(
                "INSERT INTO grupo_membros (id_grupo, id_usuario) VALUES (%s, %s)",
                (id_grupo, id_usuario_novo),
            )
            conexao.commit()
            return {"mensagem": "Membro adicionado"}
        finally:
            cursor.close()


def _checar_ultimo_admin(cursor, id_grupo: int, id_alvo: int) -> None:
    """Impede remover/rebaixar o último admin se ainda há outros membros."""
    cursor.execute(
        "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s FOR UPDATE",
        (id_grupo, id_alvo),
    )
    alvo = cursor.fetchone()
    if alvo and alvo["cargo"] == "admin":
        cursor.execute(
            "SELECT COUNT(*) as qtd FROM grupo_membros WHERE id_grupo=%s AND cargo='admin' FOR UPDATE",
            (id_grupo,),
        )
        if cursor.fetchone()["qtd"] <= 1:
            cursor.execute(
                "SELECT COUNT(*) as qtd FROM grupo_membros WHERE id_grupo=%s FOR UPDATE", (id_grupo,)
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

            if usuario_id != id_usuario_remover:
                _checar_criador(cursor, id_grupo, id_usuario_remover)
            _checar_ultimo_admin(cursor, id_grupo, id_usuario_remover)

            cursor.execute(
                "DELETE FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, id_usuario_remover),
            )
            conexao.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Membro não encontrado")
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

            cursor.execute(
                "UPDATE grupo_membros SET cargo='admin' WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, id_usuario_promover),
            )
            conexao.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Membro não encontrado ou já é admin")
            return {"mensagem": "Usuário promovido a admin"}
        finally:
            cursor.close()


def _checar_criador(cursor, id_grupo: int, id_alvo: int) -> None:
    cursor.execute(
        "SELECT criado_por FROM grupos_viagem WHERE id_grupo=%s", (id_grupo,)
    )
    grupo = cursor.fetchone()
    if grupo and grupo["criado_por"] == id_alvo:
        raise HTTPException(status_code=403, detail="O criador do grupo não pode ser rebaixado ou removido")


def rebaixar(id_grupo: int, id_usuario_rebaixar: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)
            if cargo != "admin":
                raise HTTPException(status_code=403, detail="Apenas admins podem rebaixar membros")

            _checar_criador(cursor, id_grupo, id_usuario_rebaixar)
            _checar_ultimo_admin(cursor, id_grupo, id_usuario_rebaixar)

            cursor.execute(
                "UPDATE grupo_membros SET cargo='membro' WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, id_usuario_rebaixar),
            )
            conexao.commit()
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404, detail="Membro não encontrado ou já é membro comum"
                )
            return {"mensagem": "Usuário rebaixado para membro comum"}
        finally:
            cursor.close()


def sair(id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)

            # Impedir saída com dívidas pendentes no grupo
            cursor.execute(
                """
                SELECT COALESCE(SUM(dg.valor_dividido), 0) AS divida
                FROM divisao_gastos dg
                JOIN gastos g ON dg.id_gasto = g.id_gasto
                WHERE g.id_grupo = %s AND dg.id_usuario = %s AND g.id_usuario != %s
                """,
                (id_grupo, usuario_id, usuario_id),
            )
            row = cursor.fetchone()
            if row and float(row["divida"]) > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Você possui dívidas pendentes de R$ {float(row['divida']):.2f}. Quite antes de sair.",
                )

            _checar_ultimo_admin(cursor, id_grupo, usuario_id)

            cursor.execute(
                "DELETE FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, usuario_id),
            )
            conexao.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Você não está no grupo")
            return {"mensagem": "Saiu do grupo"}
        finally:
            cursor.close()
