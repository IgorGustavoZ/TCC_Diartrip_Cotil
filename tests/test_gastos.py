"""
test_gastos.py — Testes de gastos e balanco com banco mockado.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import fake_get_db

GASTO_PAYLOAD = {
    "valor": 100.0,
    "categoria": "alimentacao",
    "descricao": "Jantar",
    "data_gasto": "2026-06-01",
    "id_usuarios_divisao": []
}


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


# =========================================================================== #
# Criar gasto
# =========================================================================== #

class TestCriarGasto:
    def test_criar_gasto_valido(self, client_usuario):
        conn = _conn_seq(
            [(1,), {"cargo": "membro"}, None],
            fetchalls={0: [{"id_usuario": 1}]}
        )
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/gastos", json=GASTO_PAYLOAD)
        assert resp.status_code == 200

    def test_valor_negativo_retorna_422(self, client_usuario):
        resp = client_usuario.post("/grupos/10/gastos", json=dict(GASTO_PAYLOAD, valor=-50.0))
        assert resp.status_code == 422

    def test_valor_zero_retorna_422(self, client_usuario):
        resp = client_usuario.post("/grupos/10/gastos", json=dict(GASTO_PAYLOAD, valor=0.0))
        assert resp.status_code == 422

    def test_usuario_fora_do_grupo_na_divisao_retorna_400(self, client_usuario):
        """Usuario nao-membro na lista de divisao retorna 400."""
        conn = _conn_seq(
            [(1,), {"cargo": "membro"}, {"qtd": 0}]
        )
        payload = dict(GASTO_PAYLOAD, id_usuarios_divisao=[999])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/gastos", json=payload)
        assert resp.status_code == 400

    def test_nao_membro_nao_pode_criar_gasto(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/gastos", json=GASTO_PAYLOAD)
        assert resp.status_code == 403

    def test_criar_gasto_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/grupos/10/gastos", json=GASTO_PAYLOAD)
        assert resp.status_code == 401


# =========================================================================== #
# Divisao com Decimal (testes unitarios)
# =========================================================================== #

class TestDivisaoDecimal:
    def test_divisao_exata(self):
        from services.gasto_service import _inserir_divisao
        cursor = MagicMock()
        _inserir_divisao(cursor, id_gasto=1, participantes=[1, 2], valor_total=100.0)
        valores = [c.args[1][2] for c in cursor.execute.call_args_list]
        assert sum(Decimal(str(v)) for v in valores) == Decimal("100.00")

    def test_divisao_com_centavo_residual(self):
        """10 / 3 = 3.33 + 3.33 + 3.34."""
        from services.gasto_service import _inserir_divisao
        cursor = MagicMock()
        _inserir_divisao(cursor, id_gasto=1, participantes=[1, 2, 3], valor_total=10.0)
        valores = [c.args[1][2] for c in cursor.execute.call_args_list]
        total = sum(Decimal(str(v)) for v in valores)
        assert total == Decimal("10.00"), f"Soma incorreta: {total}"

    def test_divisao_um_participante(self):
        from services.gasto_service import _inserir_divisao
        cursor = MagicMock()
        _inserir_divisao(cursor, id_gasto=1, participantes=[1], valor_total=99.99)
        valores = [c.args[1][2] for c in cursor.execute.call_args_list]
        assert abs(sum(Decimal(str(v)) for v in valores) - Decimal("99.99")) < Decimal("0.01")

    def test_divisao_sete_participantes_soma_correta(self):
        from services.gasto_service import _inserir_divisao
        cursor = MagicMock()
        _inserir_divisao(cursor, id_gasto=1, participantes=list(range(1, 8)), valor_total=1000.0)
        valores = [c.args[1][2] for c in cursor.execute.call_args_list]
        assert sum(Decimal(str(v)) for v in valores) == Decimal("1000.00")


# =========================================================================== #
# Balanco do grupo
# =========================================================================== #

class TestBalanco:
    def test_obter_balanco_retorna_lista(self, client_usuario):
        conn = _conn_seq(
            [(1,), {"cargo": "membro"}, None, None],
            fetchalls={
                2: [{"id_usuario": 1, "nome": "Alice"}, {"id_usuario": 2, "nome": "Bob"}],
                3: [{"user_id": 1, "total": 50.0}],
                4: [{"user_id": 2, "total": 50.0}],
            }
        )
        # fetchall na pos 2, 3, 4 — o _conn_seq so suporta fa por idx do cursor
        # vamos usar conn manual para controlar melhor
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
                c.fetchall.return_value = []
            elif call_count[0] == 2:
                c.fetchone.return_value = {"cargo": "membro"}
                c.fetchall.return_value = []
            elif call_count[0] == 3:
                c.fetchall.return_value = [
                    {"id_usuario": 1, "nome": "Alice"},
                    {"id_usuario": 2, "nome": "Bob"},
                ]
                c.fetchone.return_value = None
            elif call_count[0] == 4:
                c.fetchall.return_value = [{"user_id": 1, "total": 50.0}]
                c.fetchone.return_value = None
            else:
                c.fetchall.return_value = [{"user_id": 2, "total": 50.0}]
                c.fetchone.return_value = None
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/balanco")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# =========================================================================== #
# Deletar gasto
# =========================================================================== #

class TestDeletarGasto:
    def test_dono_pode_deletar_gasto(self, client_usuario):
        conn = _conn_seq([
            (1,),
            {"id_usuario": 1, "id_grupo": 10},
            {"cargo": "membro"},
            None,
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/gastos/1")
        assert resp.status_code == 200

    def test_outro_membro_nao_pode_deletar_gasto(self, client_usuario):
        """Token id=1, mas gasto pertence ao usuario 2."""
        conn = _conn_seq([
            (1,),
            {"id_usuario": 2, "id_grupo": 10},
            {"cargo": "membro"},
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/gastos/1")
        assert resp.status_code == 403

    def test_gasto_nao_encontrado_retorna_404(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/gastos/9999")
        assert resp.status_code == 404


# =========================================================================== #
# Atualizar gasto
# =========================================================================== #

class TestAtualizarGasto:
    def test_dono_pode_atualizar_gasto(self, client_usuario):
        conn = _conn_seq(
            [(1,), {"id_usuario": 1, "id_grupo": 10, "valor": 100.0}, {"cargo": "membro"}, None],
            fetchalls={0: [{"id_usuario": 1}]}
        )
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/gastos/1", json={
                "valor": 150.0,
                "categoria": "transporte",
                "descricao": "Passagem"
            })
        assert resp.status_code == 200

    def test_nao_dono_nao_pode_atualizar(self, client_usuario):
        """Token id=1, gasto pertence ao usuario 2, nao e admin."""
        conn = _conn_seq([
            (1,),
            {"id_usuario": 2, "id_grupo": 10, "valor": 50.0},
            {"cargo": "membro"},
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/gastos/1", json={
                "valor": 50.0,
                "categoria": "hotel",
                "descricao": "Hotel"
            })
        assert resp.status_code == 403
