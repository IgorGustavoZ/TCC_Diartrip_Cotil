from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo


def geral(id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)

            cursor.execute(
                "SELECT orcamento, nome_grupo FROM grupos_viagem WHERE id_grupo=%s", (id_grupo,)
            )
            grupo = cursor.fetchone()
            if not grupo:
                raise HTTPException(status_code=404, detail="Grupo não encontrado")

            cursor.execute(
                "SELECT SUM(valor) as total FROM gastos WHERE id_grupo=%s", (id_grupo,)
            )
            total_gastos = float(cursor.fetchone()["total"] or 0)
            orcamento = float(grupo["orcamento"] or 0)

            cursor.execute(
                """
                SELECT categoria, SUM(valor) as total, COUNT(*) as qtd
                FROM gastos
                WHERE id_grupo=%s
                GROUP BY categoria
                """,
                (id_grupo,),
            )
            categorias = cursor.fetchall()
            for cat in categorias:
                cat["total"] = round(float(cat["total"]), 2)

            return {
                "nome_grupo": grupo["nome_grupo"],
                "orcamento_total": orcamento,
                "total_consumido": round(total_gastos, 2),
                "orcamento_restante": round(orcamento - total_gastos, 2),
                "percentual_consumido": round((total_gastos / orcamento * 100), 2) if orcamento > 0 else 0,
                "distribuicao_categorias": categorias,
            }
        finally:
            cursor.close()


def pessoal(id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)

            cursor.execute(
                "SELECT SUM(valor) as total FROM gastos WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, usuario_id),
            )
            total_pago = float(cursor.fetchone()["total"] or 0)

            cursor.execute(
                """
                SELECT SUM(dg.valor_dividido) as total
                FROM divisao_gastos dg
                JOIN gastos g ON dg.id_gasto = g.id_gasto
                WHERE g.id_grupo = %s AND dg.id_usuario = %s AND g.id_usuario != %s
                """,
                (id_grupo, usuario_id, usuario_id),
            )
            total_devido = float(cursor.fetchone()["total"] or 0)

            cursor.execute(
                """
                SELECT valor, categoria, descricao, data_gasto
                FROM gastos
                WHERE id_grupo=%s AND id_usuario=%s
                ORDER BY data_gasto DESC LIMIT 5
                """,
                (id_grupo, usuario_id),
            )
            recentes = cursor.fetchall()
            for g in recentes:
                g["valor"] = round(float(g["valor"]), 2)

            return {
                "total_pago_por_mim": round(total_pago, 2),
                "minha_divida_atual": round(total_devido, 2),
                "ultimos_gastos_pessoais": recentes,
            }
        finally:
            cursor.close()


def completo(id_grupo: int, usuario_id: int) -> dict:
    """Retorna geral + pessoal + admin em uma única conexão (evita exaustão do pool)."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)

            cursor.execute(
                "SELECT orcamento, nome_grupo FROM grupos_viagem WHERE id_grupo=%s", (id_grupo,)
            )
            grupo = cursor.fetchone()
            if not grupo:
                raise HTTPException(status_code=404, detail="Grupo não encontrado")

            cursor.execute(
                "SELECT SUM(valor) as total FROM gastos WHERE id_grupo=%s", (id_grupo,)
            )
            total_gastos = float(cursor.fetchone()["total"] or 0)
            orcamento = float(grupo["orcamento"] or 0)

            cursor.execute(
                "SELECT categoria, SUM(valor) as total, COUNT(*) as qtd FROM gastos "
                "WHERE id_grupo=%s GROUP BY categoria",
                (id_grupo,),
            )
            categorias = cursor.fetchall()
            for cat in categorias:
                cat["total"] = round(float(cat["total"]), 2)

            cursor.execute(
                "SELECT SUM(valor) as total FROM gastos WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, usuario_id),
            )
            total_pago = float(cursor.fetchone()["total"] or 0)

            cursor.execute(
                """
                SELECT SUM(dg.valor_dividido) as total
                FROM divisao_gastos dg
                JOIN gastos g ON dg.id_gasto = g.id_gasto
                WHERE g.id_grupo = %s AND dg.id_usuario = %s AND g.id_usuario != %s
                """,
                (id_grupo, usuario_id, usuario_id),
            )
            total_devido = float(cursor.fetchone()["total"] or 0)

            cursor.execute(
                "SELECT valor, categoria, descricao, data_gasto FROM gastos "
                "WHERE id_grupo=%s AND id_usuario=%s ORDER BY data_gasto DESC LIMIT 5",
                (id_grupo, usuario_id),
            )
            recentes = cursor.fetchall()
            for g in recentes:
                g["valor"] = round(float(g["valor"]), 2)

            resultado: dict = {
                "geral": {
                    "nome_grupo": grupo["nome_grupo"],
                    "orcamento_total": orcamento,
                    "total_consumido": round(total_gastos, 2),
                    "orcamento_restante": round(orcamento - total_gastos, 2),
                    "percentual_consumido": round((total_gastos / orcamento * 100), 2) if orcamento > 0 else 0,
                    "distribuicao_categorias": categorias,
                },
                "pessoal": {
                    "total_pago_por_mim": round(total_pago, 2),
                    "minha_divida_atual": round(total_devido, 2),
                    "ultimos_gastos_pessoais": recentes,
                },
                "admin": None,
            }

            if cargo == "admin":
                cursor.execute(
                    """
                    SELECT u.nome, SUM(g.valor) as total
                    FROM gastos g JOIN usuarios u ON g.id_usuario = u.id_usuario
                    WHERE g.id_grupo = %s GROUP BY u.id_usuario ORDER BY total DESC
                    """,
                    (id_grupo,),
                )
                ranking = cursor.fetchall()
                for m in ranking:
                    m["total"] = round(float(m["total"]), 2)

                cursor.execute(
                    "SELECT COUNT(*) as total FROM fotos WHERE id_grupo=%s", (id_grupo,)
                )
                total_fotos = cursor.fetchone()["total"]
                cursor.execute(
                    "SELECT COUNT(*) as total FROM roteiros WHERE id_grupo=%s", (id_grupo,)
                )
                total_roteiros = cursor.fetchone()["total"]
                cursor.execute(
                    "SELECT COUNT(*) as total FROM grupo_membros WHERE id_grupo=%s", (id_grupo,)
                )
                total_membros = cursor.fetchone()["total"]

                resultado["admin"] = {
                    "estatisticas": {
                        "membros_ativos": total_membros,
                        "total_fotos_subidas": total_fotos,
                        "itens_no_roteiro": total_roteiros,
                    },
                    "ranking_contribuicao_financeira": ranking,
                }

            return resultado
        finally:
            cursor.close()


def admin(id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)
            if cargo != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="Apenas administradores podem realizar esta ação",
                )

            cursor.execute(
                """
                SELECT u.nome, SUM(g.valor) as total
                FROM gastos g
                JOIN usuarios u ON g.id_usuario = u.id_usuario
                WHERE g.id_grupo = %s
                GROUP BY u.id_usuario
                ORDER BY total DESC
                """,
                (id_grupo,),
            )
            ranking = cursor.fetchall()
            for m in ranking:
                m["total"] = round(float(m["total"]), 2)

            cursor.execute(
                "SELECT COUNT(*) as total FROM fotos WHERE id_grupo=%s", (id_grupo,)
            )
            total_fotos = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) as total FROM roteiros WHERE id_grupo=%s", (id_grupo,)
            )
            total_roteiros = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) as total FROM grupo_membros WHERE id_grupo=%s", (id_grupo,)
            )
            total_membros = cursor.fetchone()["total"]

            return {
                "estatisticas": {
                    "membros_ativos": total_membros,
                    "total_fotos_subidas": total_fotos,
                    "itens_no_roteiro": total_roteiros,
                },
                "ranking_contribuicao_financeira": ranking,
            }
        finally:
            cursor.close()
