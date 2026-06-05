import logging
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo

logger = logging.getLogger("diartrip.gasto")


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


def _inserir_divisao(cursor, id_gasto: int, participantes: list[int], valor_total: float) -> None:
    """Insere divisão usando Decimal para evitar imprecisão de ponto flutuante.
    O centavo restante vai para o último participante da lista."""
    total = Decimal(str(valor_total))
    n = len(participantes)
    parte = (total / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    resto = total - parte * (n - 1)
    for i, uid in enumerate(participantes):
        valor_dividido = float(resto if i == n - 1 else parte)
        cursor.execute(
            "INSERT INTO divisao_gastos (id_gasto, id_usuario, valor_dividido) VALUES (%s, %s, %s)",
            (id_gasto, uid, valor_dividido),
        )


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
            else:
                # Se não informado, divide entre TODOS os membros do grupo por padrão
                cursor.execute(
                    "SELECT id_usuario FROM grupo_membros WHERE id_grupo=%s",
                    (id_grupo,)
                )
                participantes = [r["id_usuario"] for r in cursor.fetchall()]

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
                _inserir_divisao(cursor, id_gasto, participantes, dados.valor)

            conexao.commit()
            logger.info(
                "Gasto registrado",
                extra={"gasto_id": id_gasto, "grupo_id": id_grupo, "user_id": usuario_id,
                       "valor": dados.valor, "participantes": len(participantes)},
            )
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

            # O quanto o usuário 'id_usuario' deve RECEBER (ele pagou, e outros devem a ele)
            cursor.execute(
                """
                SELECT g.id_usuario AS user_id,
                       COALESCE(SUM(dg.valor_dividido), 0) AS total
                FROM gastos g
                JOIN divisao_gastos dg ON dg.id_gasto = g.id_gasto
                WHERE g.id_grupo = %s AND dg.id_usuario != g.id_usuario
                GROUP BY g.id_usuario
                """,
                (id_grupo,),
            )
            receber_map = {r["user_id"]: float(r["total"]) for r in cursor.fetchall()}

            # O quanto o usuário 'id_usuario' deve PAGAR (outros pagaram, e ele deve a eles)
            cursor.execute(
                """
                SELECT dg.id_usuario AS user_id,
                       COALESCE(SUM(dg.valor_dividido), 0) AS total
                FROM divisao_gastos dg
                JOIN gastos g ON dg.id_gasto = g.id_gasto
                WHERE g.id_grupo = %s AND dg.id_usuario != g.id_usuario
                GROUP BY dg.id_usuario
                """,
                (id_grupo,),
            )
            pagar_map = {p["user_id"]: float(p["total"]) for p in cursor.fetchall()}

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
                "SELECT id_usuario, id_grupo, valor FROM gastos WHERE id_gasto=%s", (id_gasto,)
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

            # Se id_usuarios_divisao foi fornecido (mesmo que lista vazia, tratamos como desejo de atualizar)
            if dados.id_usuarios_divisao is not None:
                participantes = list(set(dados.id_usuarios_divisao))
                
                # Se a lista enviada estiver vazia, aplicamos o padrão: todos os membros do grupo
                if not participantes:
                    cursor.execute(
                        "SELECT id_usuario FROM grupo_membros WHERE id_grupo=%s",
                        (gasto["id_grupo"],)
                    )
                    participantes = [r["id_usuario"] for r in cursor.fetchall()]
                else:
                    # Validar se os participantes informados pertencem ao grupo
                    fmt = ",".join(["%s"] * len(participantes))
                    cursor.execute(
                        f"SELECT COUNT(*) as qtd FROM grupo_membros "
                        f"WHERE id_grupo=%s AND id_usuario IN ({fmt})",
                        [gasto["id_grupo"]] + participantes,
                    )
                    if cursor.fetchone()["qtd"] != len(participantes):
                        raise HTTPException(
                            status_code=400,
                            detail="Um ou mais usuários da divisão não pertencem ao grupo",
                        )
                
                cursor.execute("DELETE FROM divisao_gastos WHERE id_gasto=%s", (id_gasto,))
                if participantes:
                    _inserir_divisao(cursor, id_gasto, participantes, dados.valor)
            else:
                # Se não informou id_usuarios_divisao, apenas recalcula para os atuais (devido a mudança de valor)
                cursor.execute(
                    "SELECT id_usuario FROM divisao_gastos WHERE id_gasto=%s", (id_gasto,)
                )
                participantes_existentes = [r["id_usuario"] for r in cursor.fetchall()]
                if participantes_existentes:
                    cursor.execute("DELETE FROM divisao_gastos WHERE id_gasto=%s", (id_gasto,))
                    _inserir_divisao(cursor, id_gasto, participantes_existentes, dados.valor)

            conexao.commit()
            logger.info(
                "Gasto atualizado",
                extra={"gasto_id": id_gasto, "user_id": usuario_id, "valor": dados.valor},
            )
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

            cursor.execute("DELETE FROM divisao_gastos WHERE id_gasto=%s", (id_gasto,))
            cursor.execute("DELETE FROM gastos WHERE id_gasto=%s", (id_gasto,))
            conexao.commit()
            logger.info(
                "Gasto removido",
                extra={"gasto_id": id_gasto, "user_id": usuario_id},
            )
            return {"mensagem": "Gasto removido"}
        finally:
            cursor.close()
