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
                SELECT g.id_gasto, g.valor, g.categoria, g.descricao,
                       g.data_gasto, u.nome, u.id_usuario
                FROM gastos g
                JOIN usuarios u ON g.id_usuario = u.id_usuario
                WHERE g.id_grupo = %s
                ORDER BY g.data_gasto DESC
                """,
                (id_grupo,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def criar(id_grupo: int, usuario_id: int, dados) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)

            participantes: list[int] = []
            if dados.id_usuarios_divisao:
                participantes = list(set(dados.id_usuarios_divisao))
                fmt = ",".join(["%s"] * len(participantes))
                cursor.execute(
                    f"SELECT COUNT(*) as qtd FROM grupo_membros "
                    f"WHERE id_grupo=%s AND id_usuario IN ({fmt})",
                    [id_grupo] + participantes,
                )
                if cursor.fetchone()["qtd"] != len(participantes):
                    raise HTTPException(
                        status_code=400,
                        detail="Um ou mais usuários da divisão não pertencem ao grupo",
                    )

            cursor.execute(
                """
                INSERT INTO gastos (id_grupo, id_usuario, valor, categoria, descricao, data_gasto)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (id_grupo, usuario_id, dados.valor, dados.categoria,
                 dados.descricao, dados.data_gasto),
            )
            id_gasto = cursor.lastrowid

            if participantes:
                valor_por_pessoa = dados.valor / len(participantes)
                for uid in participantes:
                    cursor.execute(
                        "INSERT INTO divisao_gastos (id_gasto, id_usuario, valor_dividido) "
                        "VALUES (%s, %s, %s)",
                        (id_gasto, uid, valor_por_pessoa),
                    )

            conexao.commit()
            return {"mensagem": "Gasto registrado", "id": id_gasto}
        finally:
            cursor.close()


def obter_balanco(id_grupo: int, usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)

            cursor.execute(
                """
                SELECT u.id_usuario, u.nome
                FROM usuarios u
                JOIN grupo_membros gm ON u.id_usuario = gm.id_usuario
                WHERE gm.id_grupo = %s
                """,
                (id_grupo,),
            )
            membros = cursor.fetchall()

            cursor.execute(
                """
                SELECT g.id_usuario AS id_usuario,
                       COALESCE(SUM(dg.valor_dividido), 0) AS total
                FROM gastos g
                JOIN divisao_gastos dg ON dg.id_gasto = g.id_gasto
                WHERE g.id_grupo = %s AND dg.id_usuario != g.id_usuario
                GROUP BY g.id_usuario
                """,
                (id_grupo,),
            )
            receber_map = {r["id_usuario"]: float(r["total"]) for r in cursor.fetchall()}

            cursor.execute(
                """
                SELECT dg.id_usuario AS id_usuario,
                       COALESCE(SUM(dg.valor_dividido), 0) AS total
                FROM divisao_gastos dg
                JOIN gastos g ON dg.id_gasto = g.id_gasto
                WHERE g.id_grupo = %s AND dg.id_usuario != g.id_usuario
                GROUP BY dg.id_usuario
                """,
                (id_grupo,),
            )
            pagar_map = {p["id_usuario"]: float(p["total"]) for p in cursor.fetchall()}

            return [
                {
                    "id_usuario": m["id_usuario"],
                    "nome": m["nome"],
                    "saldo": round(
                        receber_map.get(m["id_usuario"], 0.0) - pagar_map.get(m["id_usuario"], 0.0),
                        2,
                    ),
                    "a_receber": round(receber_map.get(m["id_usuario"], 0.0), 2),
                    "a_pagar": round(pagar_map.get(m["id_usuario"], 0.0), 2),
                }
                for m in membros
            ]
        finally:
            cursor.close()


def atualizar(id_gasto: int, dados, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_usuario, id_grupo FROM gastos WHERE id_gasto=%s", (id_gasto,)
            )
            gasto = cursor.fetchone()
            if not gasto:
                raise HTTPException(status_code=404, detail="Gasto não encontrado")

            cargo = checar_membro_grupo(cursor, gasto["id_grupo"], usuario_id)
            if usuario_id != gasto["id_usuario"] and cargo != "admin":
                raise HTTPException(status_code=403, detail="Sem permissão")

            cursor.execute(
                "UPDATE gastos SET valor=%s, categoria=%s, descricao=%s WHERE id_gasto=%s",
                (dados.valor, dados.categoria, dados.descricao, id_gasto),
            )
            conexao.commit()
            return {"mensagem": "Gasto atualizado"}
        finally:
            cursor.close()


def deletar(id_gasto: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_usuario, id_grupo FROM gastos WHERE id_gasto=%s", (id_gasto,)
            )
            gasto = cursor.fetchone()
            if not gasto:
                raise HTTPException(status_code=404, detail="Gasto não encontrado")

            cargo = checar_membro_grupo(cursor, gasto["id_grupo"], usuario_id)
            if usuario_id != gasto["id_usuario"] and cargo != "admin":
                raise HTTPException(status_code=403, detail="Sem permissão")

            cursor.execute("DELETE FROM gastos WHERE id_gasto=%s", (id_gasto,))
            conexao.commit()
            return {"mensagem": "Gasto removido"}
        finally:
            cursor.close()
