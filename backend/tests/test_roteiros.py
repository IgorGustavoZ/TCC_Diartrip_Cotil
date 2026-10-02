"""
test_roteiros.py — Testes de roteiros com banco mockado.
"""
from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db, fake_roteiro

ROTEIRO_PAYLOAD = {
    "id_grupo": 10,
    "titulo": "Dia 1 em Paris",
    "descricao": "Visitar Torre Eiffel e Louvre"
}


def _conn_seq(fetchones):
    fetch_idx = [0]

    def factory(**kw):
        c = MagicMock()
        c.rowcount = 1
        c.lastrowid = 1

        def _fetchone():
            i = fetch_idx[0]
            fetch_idx[0] += 1
            return fetchones[i] if i < len(fetchones) else None

        c.fetchone.side_effect = _fetchone
        c.fetchall.return_value = []
        return c

    conn = MagicMock()
    conn.cursor.side_effect = factory
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn



class TestCriarRoteiro:
    def test_admin_pode_criar_roteiro(self, client_admin):
        conn = _conn_seq([(99,), {"cargo": "admin"}, None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.post("/roteiros", json=ROTEIRO_PAYLOAD)
        assert resp.status_code == 201

    def test_membro_comum_nao_pode_criar_roteiro(self, client_usuario):
        # Só o admin do grupo pode adicionar roteiro — a ação é
        # administrativa (igual já era pra editar/deletar).
        conn = _conn_seq([(1,), {"cargo": "membro"}])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/roteiros", json=ROTEIRO_PAYLOAD)
        assert resp.status_code == 403

    def test_nao_membro_nao_pode_criar_roteiro(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/roteiros", json=ROTEIRO_PAYLOAD)
        assert resp.status_code == 403

    def test_criar_roteiro_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/roteiros", json=ROTEIRO_PAYLOAD)
        assert resp.status_code == 401

    def test_titulo_muito_longo_retorna_422(self, client_usuario):
        payload = dict(ROTEIRO_PAYLOAD, titulo="A" * 201)
        resp = client_usuario.post("/roteiros", json=payload)
        assert resp.status_code == 422



class TestListarRoteiros:
    def test_listar_roteiros_do_grupo(self, client_usuario):
        roteiros = [fake_roteiro(1), fake_roteiro(2)]
        fetch_idx = [0]
        fetchall_idx = [0]
        fetchones = [(1,), {"cargo": "membro"}]

        def factory(**kw):
            c = MagicMock()
            c.rowcount = 1

            def _fetchone():
                i = fetch_idx[0]
                fetch_idx[0] += 1
                return fetchones[i] if i < len(fetchones) else None

            def _fetchall():
                i = fetchall_idx[0]
                fetchall_idx[0] += 1
                return roteiros if i == 0 else []

            c.fetchone.side_effect = _fetchone
            c.fetchall.side_effect = _fetchall
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/roteiros")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)



class TestAtualizarRoteiro:
    def test_admin_pode_atualizar_roteiro(self, client_admin):
        conn = _conn_seq([(99,), {"id_grupo": 10}, {"cargo": "admin"}, None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/roteiros/1", json={
                "titulo": "Titulo atualizado",
                "descricao": "Nova descricao"
            })
        assert resp.status_code == 200

    def test_membro_nao_pode_atualizar_roteiro(self, client_usuario):
        conn = _conn_seq([(1,), {"id_grupo": 10}, {"cargo": "membro"}])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/roteiros/1", json={
                "titulo": "Titulo",
                "descricao": "Descricao"
            })
        assert resp.status_code == 403

    def test_roteiro_inexistente_retorna_404(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/roteiros/9999", json={
                "titulo": "T",
                "descricao": "D"
            })
        assert resp.status_code == 404



class TestDeletarRoteiro:
    def test_admin_pode_deletar_roteiro(self, client_admin):
        conn = _conn_seq([(99,), {"id_grupo": 10}, {"cargo": "admin"}, None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.delete("/roteiros/1")
        assert resp.status_code == 200

    def test_membro_nao_pode_deletar_roteiro(self, client_usuario):
        conn = _conn_seq([(1,), {"id_grupo": 10}, {"cargo": "membro"}])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/roteiros/1")
        assert resp.status_code == 403

    def test_nao_membro_nao_pode_deletar_roteiro(self, client_usuario):
        conn = _conn_seq([(1,), {"id_grupo": 10}, None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/roteiros/1")
        assert resp.status_code == 403


class TestMoverRoteiro:
    def _conn_mover(self, usuario_fetchone, itens):
        # mover() consulta: id_usuario (auth), o item atual, checar_membro_grupo
        # (cargo), e por fim a lista completa do grupo (fetchall) pra achar a
        # posição dentro do mesmo "dia".
        fetchones = usuario_fetchone
        fetch_idx = [0]

        def factory(**kw):
            c = MagicMock()
            c.rowcount = 1

            def _fetchone():
                i = fetch_idx[0]
                fetch_idx[0] += 1
                return fetchones[i] if i < len(fetchones) else None

            c.fetchone.side_effect = _fetchone
            c.fetchall.return_value = itens
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()
        return conn

    def test_admin_pode_mover_item_para_baixo(self, client_admin):
        atual = {"id_grupo": 10, "titulo": "Dia 1 · 09:00 — Café", "ordem": 0}
        itens = [
            {"id_roteiro": 1, "titulo": "Dia 1 · 09:00 — Café", "ordem": 0},
            {"id_roteiro": 2, "titulo": "Dia 1 · 11:00 — Museu", "ordem": 1},
        ]
        conn = self._conn_mover([(99,), atual, {"cargo": "admin"}], itens)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.patch("/roteiros/1/mover", json={"direcao": "baixo"})
        assert resp.status_code == 200

    def test_primeiro_item_do_dia_nao_pode_mover_para_cima(self, client_admin):
        atual = {"id_grupo": 10, "titulo": "Dia 1 · 09:00 — Café", "ordem": 0}
        itens = [
            {"id_roteiro": 1, "titulo": "Dia 1 · 09:00 — Café", "ordem": 0},
            {"id_roteiro": 2, "titulo": "Dia 1 · 11:00 — Museu", "ordem": 1},
        ]
        conn = self._conn_mover([(99,), atual, {"cargo": "admin"}], itens)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.patch("/roteiros/1/mover", json={"direcao": "cima"})
        assert resp.status_code == 200
        assert "limite" in resp.json()["mensagem"].lower()

    def test_mover_nao_atravessa_dias_diferentes(self, client_admin):
        # Último item do Dia 1 não pode "descer" para o Dia 2 — são grupos
        # independentes (extraídos do texto do título, _dia_de).
        atual = {"id_grupo": 10, "titulo": "Dia 1 · 11:00 — Museu", "ordem": 1}
        itens = [
            {"id_roteiro": 1, "titulo": "Dia 1 · 09:00 — Café", "ordem": 0},
            {"id_roteiro": 2, "titulo": "Dia 1 · 11:00 — Museu", "ordem": 1},
            {"id_roteiro": 3, "titulo": "Dia 2 · 09:00 — Praia", "ordem": 2},
        ]
        conn = self._conn_mover([(99,), atual, {"cargo": "admin"}], itens)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.patch("/roteiros/2/mover", json={"direcao": "baixo"})
        assert resp.status_code == 200
        assert "limite" in resp.json()["mensagem"].lower()

    def test_membro_comum_nao_pode_mover_roteiro(self, client_usuario):
        atual = {"id_grupo": 10, "titulo": "Dia 1 · 09:00 — Café", "ordem": 0}
        conn = self._conn_mover([(1,), atual, {"cargo": "membro"}], [])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.patch("/roteiros/1/mover", json={"direcao": "baixo"})
        assert resp.status_code == 403

    def test_roteiro_inexistente_retorna_404(self, client_admin):
        conn = self._conn_mover([(99,), None], [])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.patch("/roteiros/9999/mover", json={"direcao": "baixo"})
        assert resp.status_code == 404

    def test_direcao_invalida_retorna_422(self, client_admin):
        # Validado pelo próprio Pydantic (RoteiroMover.direcao), nem chega
        # a tocar no banco.
        resp = client_admin.patch("/roteiros/1/mover", json={"direcao": "lado"})
        assert resp.status_code == 422


