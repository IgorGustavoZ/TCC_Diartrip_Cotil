"""
test_dashboard.py — Testes do dashboard com banco mockado.
"""
from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db

_GRUPO_ROW = {"orcamento": 5000.0, "nome_grupo": "Viagem Paris"}
_TOTAL_ROW = {"total": 1250.0}
_CAT_ROWS = [{"categoria": "alimentacao", "total": 500.0, "qtd": 5}]
_RANKING = [{"nome": "Alice", "total": 750.0}]


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
# Dashboard geral
# =========================================================================== #

class TestDashboardGeral:
    def test_membro_acessa_dashboard_geral(self, client_usuario):
        conn = _conn_seq(
            [(1,), {"cargo": "membro"}, _GRUPO_ROW, _TOTAL_ROW],
            fetchalls={0: _CAT_ROWS}
        )
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/dashboard/geral")
        assert resp.status_code == 200
        data = resp.json()
        assert "orcamento_total" in data
        assert "total_consumido" in data

    def test_nao_membro_nao_acessa_dashboard_geral(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/dashboard/geral")
        assert resp.status_code == 403

    def test_dashboard_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/grupos/10/dashboard/geral")
        assert resp.status_code == 401


# =========================================================================== #
# Dashboard pessoal
# =========================================================================== #

class TestDashboardPessoal:
    def test_membro_acessa_dashboard_pessoal(self, client_usuario):
        conn = _conn_seq(
            [(1,), {"cargo": "membro"}, {"total": 500.0}, {"total": 100.0}],
            fetchalls={0: [{"valor": 100.0, "categoria": "hotel",
                           "descricao": "Hotel", "data_gasto": "2026-06-01"}]}
        )
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/dashboard/pessoal")
        assert resp.status_code == 200
        assert "total_pago_por_mim" in resp.json()

    def test_nao_membro_nao_acessa_dashboard_pessoal(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/dashboard/pessoal")
        assert resp.status_code == 403


# =========================================================================== #
# Dashboard completo
# =========================================================================== #

class TestDashboardCompleto:
    def test_membro_acessa_dashboard_completo(self, client_usuario):
        conn = _conn_seq(
            [(1,), {"cargo": "membro"}, _GRUPO_ROW, _TOTAL_ROW,
             _TOTAL_ROW, {"total": 50.0}],
            fetchalls={
                0: _CAT_ROWS,
                1: [{"valor": 100.0, "categoria": "hotel",
                     "descricao": "H", "data_gasto": "2026-06-01"}],
            }
        )
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "geral" in data
        assert "pessoal" in data

    def test_admin_recebe_secao_admin(self, client_admin):
        """Admin recebe secao 'admin' no dashboard completo."""
        conn = _conn_seq(
            [(99,), {"cargo": "admin"}, _GRUPO_ROW, _TOTAL_ROW,
             _TOTAL_ROW, {"total": 0.0},
             {"total": 3}, {"total": 10}, {"total": 2}],
            fetchalls={
                0: _CAT_ROWS,
                1: [],
                2: _RANKING,
            }
        )
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.get("/grupos/10/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "admin" in data
        assert data.get("admin") is not None


# =========================================================================== #
# Dashboard admin exclusivo
# =========================================================================== #

class TestDashboardAdmin:
    def test_admin_acessa_dashboard_admin(self, client_admin):
        conn = _conn_seq(
            [(99,), {"cargo": "admin"},
             {"total": 3}, {"total": 10}, {"total": 2}],
            fetchalls={0: _RANKING}
        )
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.get("/grupos/10/dashboard/admin")
        assert resp.status_code == 200
        assert "estatisticas" in resp.json()

    def test_membro_nao_acessa_dashboard_admin(self, client_usuario):
        conn = _conn_seq([(1,), {"cargo": "membro"}])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/dashboard/admin")
        assert resp.status_code == 403
