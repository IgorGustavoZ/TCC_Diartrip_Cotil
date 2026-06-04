"""
test_chat_ia.py — Testes do chat com IA (OpenRouter mockado).
"""
from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db


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


def _fake_ia(texto="Resposta da IA."):
    choice = MagicMock()
    choice.message.content = texto
    resp = MagicMock()
    resp.choices = [choice]
    return resp


_GRUPO = {
    "nome_grupo": "Paris 2026",
    "destino_principal": "Paris",
    "data_inicio": "2026-06-01",
    "data_fim": "2026-06-15",
    "orcamento": 5000,
    "tipo_viagem": "lazer",
}


# =========================================================================== #
# Perguntas validas e invalidas
# =========================================================================== #

class TestChatIA:
    def test_pergunta_valida_retorna_resposta(self, client_usuario):
        """Pergunta valida chama a IA e retorna resposta."""
        # Primeira conexao: auth + checar_membro + SELECT grupo + historico
        # Segunda conexao: INSERT historico
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            c.lastrowid = 1
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            elif call_count[0] == 2:
                c.fetchone.return_value = {"cargo": "membro"}
            elif call_count[0] == 3:
                c.fetchone.return_value = _GRUPO
            else:
                c.fetchone.return_value = None
            c.fetchall.return_value = []
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.chat_service._client") as mock_client:
            mock_client.chat.completions.create.return_value = _fake_ia("Sugiro o Louvre.")
            resp = client_usuario.post("/chat", json={
                "pergunta": "Quais museus visitar em Paris?",
                "id_grupo": 10,
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "resposta" in data
        assert "pergunta" in data

    def test_pergunta_vazia_retorna_422(self, client_usuario):
        """Pergunta string vazia — min_length=1 => 422."""
        resp = client_usuario.post("/chat", json={"pergunta": "", "id_grupo": 10})
        assert resp.status_code in (400, 422)

    def test_pergunta_muito_longa_retorna_422(self, client_usuario):
        """Pergunta > 1000 chars => 422."""
        resp = client_usuario.post("/chat", json={"pergunta": "A" * 1001, "id_grupo": 10})
        assert resp.status_code == 422

    def test_openrouter_indisponivel_retorna_502(self, client_usuario):
        """OpenRouter offline => 502."""
        conn = _conn_seq([(1,), {"cargo": "membro"}, _GRUPO])
        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.chat_service._client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("Connection refused")
            resp = client_usuario.post("/chat", json={"pergunta": "Onde jantar?", "id_grupo": 10})
        assert resp.status_code == 502

    def test_nao_membro_nao_pode_usar_chat_ia(self, client_usuario):
        """Nao membro do grupo recebe 403."""
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/chat", json={"pergunta": "Teste", "id_grupo": 10})
        assert resp.status_code == 403

    def test_chat_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/chat", json={"pergunta": "Teste", "id_grupo": 10})
        assert resp.status_code == 401

    def test_listar_historico_chat(self, client_usuario):
        historico = [{
            "id_chat": 1, "id_grupo": 10,
            "pergunta": "Onde jantar?",
            "resposta": "No Le Jules Verne.",
            "data_interacao": "2026-06-01T20:00:00",
        }]
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchall.return_value = historico
                c.fetchone.return_value = None
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/chat")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_resposta_nao_contem_system_prompt(self, client_usuario):
        """System prompt nao deve vazar na resposta HTTP."""
        conn = _conn_seq([(1,), {"cargo": "membro"}, _GRUPO])
        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.chat_service._client") as mock_client:
            mock_client.chat.completions.create.return_value = _fake_ia("Visite o Louvre.")
            resp = client_usuario.post("/chat", json={
                "pergunta": "Que horas abre o Louvre?",
                "id_grupo": 10,
            })

        body = resp.text
        assert "Seu papel é exclusivamente" not in body
        assert "Regras (não negociáveis)" not in body


# =========================================================================== #
# Rate limit
# =========================================================================== #

class TestRateLimitChatIA:
    def test_rate_limit_retorna_429(self, client_usuario):
        from fastapi import HTTPException
        conn = _conn_seq([(1,)])

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.chat_service.verificar_rate_limit",
                   side_effect=HTTPException(status_code=429, detail="Muitas tentativas")):
            resp = client_usuario.post("/chat", json={"pergunta": "Teste", "id_grupo": 10})

        assert resp.status_code == 429
