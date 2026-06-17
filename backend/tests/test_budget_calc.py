"""
test_budget_calc.py — Testes de calculo financeiro e balanco.
"""
from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db


def _conn_seq(fetchones, fetchalls=None):
    fa = fetchalls or {}
    fetch_idx = [0]
    fetchall_idx = [0]

    def factory(**kw):
        c = MagicMock()
        c.rowcount = 1
        c.lastrowid = 1

        def _fetchone():
            i = fetch_idx[0]
            fetch_idx[0] += 1
            return fetchones[i] if i < len(fetchones) else None

        def _fetchall():
            i = fetchall_idx[0]
            fetchall_idx[0] += 1
            return fa.get(i, [])

        c.fetchone.side_effect = _fetchone
        c.fetchall.side_effect = _fetchall
        return c

    conn = MagicMock()
    conn.cursor.side_effect = factory
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


def test_calculo_orcamento_dashboard(client_usuario):
    """Dashboard geral mostra total consumido e orcamento restante corretos."""
    orcamento = 5000.00
    total_gastos = 1250.50

    conn = _conn_seq(
        [
            (1,),
            {"cargo": "membro"},
            {"orcamento": orcamento, "nome_grupo": "Teste Financeiro"},
            {"total": total_gastos},
        ],
    )

    with patch("database.get_db", fake_get_db(conn)):
        resp = client_usuario.get("/grupos/10/dashboard/geral")

    assert resp.status_code == 200
    dados = resp.json()

    assert dados["total_consumido"] == total_gastos
    assert dados["orcamento_restante"] == round(orcamento - total_gastos, 2)


def test_balanco_entre_membros(client_usuario):
    """Balanco distribui corretamente entre quem pagou e quem deve."""
    conn = _conn_seq(
        [(1,), {"cargo": "membro"}],
        fetchalls={
            0: [
                {"id_usuario": 1, "nome": "Tester"},
                {"id_usuario": 2, "nome": "Outro"},
            ],
            1: [{"user_id": 1, "total": 50.0}],
            2: [{"user_id": 2, "total": 50.0}],
        },
    )

    with patch("database.get_db", fake_get_db(conn)):
        resp = client_usuario.get("/grupos/10/balanco")

    assert resp.status_code == 200
    balanco = resp.json()

    meu_balanco = next((m for m in balanco if m["id_usuario"] == 1), None)
    outro_balanco = next((m for m in balanco if m["id_usuario"] == 2), None)

    assert meu_balanco is not None, "Usuario 1 nao apareceu no balanco"
    assert outro_balanco is not None, "Usuario 2 nao apareceu no balanco"
    assert float(meu_balanco["a_receber"]) == 50.00
    assert float(meu_balanco["saldo"]) == 50.00
    assert float(outro_balanco["a_pagar"]) == 50.00
    assert float(outro_balanco["saldo"]) == -50.00
