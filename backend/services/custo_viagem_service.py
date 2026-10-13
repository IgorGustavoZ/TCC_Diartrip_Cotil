"""Custos da viagem — opções de passagem/hospedagem pesquisadas via SerpApi
e salvas pelos membros do grupo. Fluxo de status: salva -> orcamento ->
paga/descartada. "Marcar como paga" reaproveita gasto_service.criar() de
verdade (nunca duplica a lógica de divisão/validação de despesas) — ver
alembic/versions/014_opcoes_custo.py pro desenho da tabela.
"""
import json
import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo
from services import gasto_service, dashboard_service

logger = logging.getLogger("diartrip.custo_viagem")

_TIPOS_VALIDOS = {"voo", "hospedagem"}
_CATEGORIA_POR_TIPO = {"voo": "transporte", "hospedagem": "hospedagem"}


class _GastoAdapter:
    """Mesmo shape que gasto_service.criar() espera (dados.valor/.categoria/
    .descricao/.data_gasto/.id_usuarios_divisao) — adapta a opção salva pro
    formato já usado na criação manual de gastos, sem duplicar a função."""
    def __init__(self, valor, categoria, descricao, data_gasto, id_usuarios_divisao):
        self.valor = valor
        self.categoria = categoria
        self.descricao = descricao
        self.data_gasto = data_gasto
        self.id_usuarios_divisao = id_usuarios_divisao or []


def _normalizar(opcao: dict) -> dict:
    opcao["preco"] = float(opcao["preco"])
    detalhes = opcao.get("detalhes")
    if isinstance(detalhes, str):
        opcao["detalhes"] = json.loads(detalhes) if detalhes else None
    return opcao


def _buscar_opcao_do_grupo(cursor, id_opcao: int, id_grupo: int, usuario_id: int) -> dict:
    """Checa que o usuário pertence a id_grupo E que a opção pertence
    exatamente a esse grupo — nunca basta a opção existir, ela precisa
    pertencer ao grupo informado na URL (evita acessar opção de outro grupo
    só adivinhando o id_opcao)."""
    checar_membro_grupo(cursor, id_grupo, usuario_id)
    cursor.execute("SELECT * FROM opcoes_custo WHERE id_opcao=%s", (id_opcao,))
    opcao = cursor.fetchone()
    if not opcao or opcao["id_grupo"] != id_grupo:
        raise HTTPException(status_code=404, detail="Opção não encontrada")
    return _normalizar(opcao)


def salvar(id_grupo: int, usuario_id: int, dados) -> dict:
    if dados.tipo not in _TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Tipo deve ser 'voo' ou 'hospedagem'")

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                """
                INSERT INTO opcoes_custo
                    (id_grupo, id_usuario, tipo, nome, origem, destino,
                     data_ida, data_volta, preco, moeda, link_externo, detalhes, data_consulta)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    id_grupo, usuario_id, dados.tipo, dados.nome.strip(),
                    dados.origem, dados.destino, dados.data_ida, dados.data_volta,
                    dados.preco, dados.moeda or "BRL", dados.link_externo,
                    json.dumps(dados.detalhes) if dados.detalhes else None,
                    datetime.now(timezone.utc).replace(tzinfo=None),
                ),
            )
            logger.info(
                "Opção de custo salva",
                extra={"grupo_id": id_grupo, "user_id": usuario_id, "tipo": dados.tipo},
            )
            return {"mensagem": "Opção salva", "id": cursor.lastrowid}
        finally:
            cursor.close()


def listar(id_grupo: int, usuario_id: int, tipo: str | None = None, status: str | None = None) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            sql = "SELECT * FROM opcoes_custo WHERE id_grupo=%s"
            params: list = [id_grupo]
            if tipo:
                sql += " AND tipo=%s"
                params.append(tipo)
            if status:
                sql += " AND status=%s"
                params.append(status)
            sql += " ORDER BY data_criacao DESC"
            cursor.execute(sql, tuple(params))
            return [_normalizar(o) for o in cursor.fetchall()]
        finally:
            cursor.close()


def marcar_orcamento(id_opcao: int, id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            opcao = _buscar_opcao_do_grupo(cursor, id_opcao, id_grupo, usuario_id)
            if opcao["status"] not in ("salva", "orcamento"):
                raise HTTPException(
                    status_code=400,
                    detail="Só é possível adicionar ao orçamento uma opção salva",
                )
            cursor.execute(
                "UPDATE opcoes_custo SET status='orcamento' WHERE id_opcao=%s", (id_opcao,)
            )
            return {"mensagem": "Adicionada ao orçamento planejado"}
        finally:
            cursor.close()


def descartar(id_opcao: int, id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            opcao = _buscar_opcao_do_grupo(cursor, id_opcao, id_grupo, usuario_id)
            if opcao["status"] == "paga":
                raise HTTPException(
                    status_code=400,
                    detail="Não é possível descartar uma opção já paga — gerencie a despesa na aba Gastos",
                )
            cursor.execute(
                "UPDATE opcoes_custo SET status='descartada' WHERE id_opcao=%s", (id_opcao,)
            )
            return {"mensagem": "Opção descartada"}
        finally:
            cursor.close()


def excluir(id_opcao: int, id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            opcao = _buscar_opcao_do_grupo(cursor, id_opcao, id_grupo, usuario_id)
            if opcao["status"] == "paga":
                raise HTTPException(
                    status_code=400,
                    detail="Não é possível excluir uma opção já paga — remova a despesa vinculada na aba Gastos primeiro",
                )
            cursor.execute("DELETE FROM opcoes_custo WHERE id_opcao=%s", (id_opcao,))
            return {"mensagem": "Opção excluída"}
        finally:
            cursor.close()


def marcar_pago(id_opcao: int, id_grupo: int, usuario_id: int, dados) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            opcao = _buscar_opcao_do_grupo(cursor, id_opcao, id_grupo, usuario_id)
            if opcao["status"] == "paga":
                raise HTTPException(status_code=409, detail="Esta opção já foi marcada como paga")
            estado_anterior = opcao["status"]

            # Reivindica a opção ANTES de criar o gasto: o UPDATE com
            # "status != 'paga'" no WHERE é resolvido atomicamente pelo MySQL
            # (lock de linha), então duas requisições simultâneas pro mesmo
            # id_opcao nunca conseguem as duas passar daqui — só uma segue
            # e cria o gasto; a outra recebe rowcount=0 e falha com 409,
            # evitando o lançamento duplicado.
            cursor.execute(
                "UPDATE opcoes_custo SET status='paga' WHERE id_opcao=%s AND status != 'paga'",
                (id_opcao,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=409, detail="Esta opção já foi paga")
        finally:
            cursor.close()

    try:
        categoria = _CATEGORIA_POR_TIPO[opcao["tipo"]]
        valor = dados.valor if dados.valor is not None else opcao["preco"]
        descricao = dados.descricao or opcao["nome"]
        gasto_dados = _GastoAdapter(
            valor, categoria, descricao, dados.data_gasto, dados.id_usuarios_divisao
        )
        resultado_gasto = gasto_service.criar(id_grupo, usuario_id, gasto_dados)
    except Exception:
        with get_db() as conexao_rb:
            cursor_rb = conexao_rb.cursor()
            try:
                cursor_rb.execute(
                    "UPDATE opcoes_custo SET status=%s WHERE id_opcao=%s",
                    (estado_anterior, id_opcao),
                )
            finally:
                cursor_rb.close()
        raise

    with get_db() as conexao2:
        cursor2 = conexao2.cursor()
        try:
            cursor2.execute(
                "UPDATE opcoes_custo SET id_gasto=%s WHERE id_opcao=%s",
                (resultado_gasto["id"], id_opcao),
            )
        finally:
            cursor2.close()

    logger.info(
        "Pagamento registrado a partir de opção de custo",
        extra={"grupo_id": id_grupo, "user_id": usuario_id, "id_opcao": id_opcao,
               "id_gasto": resultado_gasto["id"]},
    )
    return {"mensagem": "Pagamento registrado", "id_gasto": resultado_gasto["id"]}


def resumo_financeiro(id_grupo: int, usuario_id: int) -> dict:
    """Reaproveita dashboard_service.geral() pros números que já existem
    (orçamento total, consumido, restante, distribuição por categoria) —
    nunca recalcula isso em paralelo. Só soma, à parte, o que está
    'adicionado ao orçamento' nas opções salvas (planejado_*), que é um
    número NOVO e não deve ser somado ao orcamento_restante aqui: ele fica
    só como informação complementar, pra não contar o mesmo valor duas vezes
    antes de a despesa ser de fato registrada."""
    geral = dashboard_service.geral(id_grupo, usuario_id)

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT tipo, COALESCE(SUM(preco),0) AS total FROM opcoes_custo "
                "WHERE id_grupo=%s AND status='orcamento' GROUP BY tipo",
                (id_grupo,),
            )
            planejado = {r["tipo"]: float(r["total"]) for r in cursor.fetchall()}
        finally:
            cursor.close()

    categorias_gastos = {c["categoria"]: c["total"] for c in geral["distribuicao_categorias"]}

    return {
        "orcamento_total": geral["orcamento_total"],
        "total_consumido": geral["total_consumido"],
        "orcamento_restante": geral["orcamento_restante"],
        "planejado_voos": round(planejado.get("voo", 0.0), 2),
        "planejado_hospedagem": round(planejado.get("hospedagem", 0.0), 2),
        "gastos_categoria_transporte": round(categorias_gastos.get("transporte", 0.0), 2),
        "gastos_categoria_hospedagem": round(categorias_gastos.get("hospedagem", 0.0), 2),
    }
