"""
test_usuarios.py — Testes de CRUD de usuarios com banco mockado.
"""
from unittest.mock import MagicMock, patch

from tests.conftest import make_cursor, make_connection, fake_get_db, fake_usuario, JPEG_MAGIC


# =========================================================================== #
# Criar usuario
# =========================================================================== #

class TestCriarUsuario:
    def test_criar_usuario_valido(self, client):
        cur = MagicMock()
        cur.lastrowid = 5
        cur.rowcount = 1
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/usuarios", json={
                "nome": "Joao Silva",
                "email": "joao@example.com",
                "senha": "SenhaForte1"
            })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data or "mensagem" in data

    def test_criar_usuario_email_invalido_retorna_422(self, client):
        resp = client.post("/usuarios", json={
            "nome": "Teste",
            "email": "nao-e-email",
            "senha": "SenhaForte1"
        })
        assert resp.status_code == 422

    def test_criar_usuario_email_duplicado_retorna_409(self, client):
        with patch("services.usuario_service.criar") as mock_criar:
            from fastapi import HTTPException
            mock_criar.side_effect = HTTPException(status_code=409, detail="Email ja cadastrado")
            resp = client.post("/usuarios", json={
                "nome": "Duplicado",
                "email": "dup@example.com",
                "senha": "SenhaForte1"
            })
        assert resp.status_code == 409

    def test_criar_usuario_sem_nome_retorna_422(self, client):
        resp = client.post("/usuarios", json={
            "email": "sem_nome@example.com",
            "senha": "SenhaForte1"
        })
        assert resp.status_code == 422

    def test_criar_usuario_sem_senha_retorna_422(self, client):
        resp = client.post("/usuarios", json={
            "nome": "Sem Senha",
            "email": "semsenhq@example.com"
        })
        assert resp.status_code == 422

    def test_criar_usuario_senha_fraca_retorna_422(self, client):
        """Senha sem maiuscula e numero deve ser rejeitada."""
        resp = client.post("/usuarios", json={
            "nome": "Fraco",
            "email": "fraco@example.com",
            "senha": "senhafraca"
        })
        assert resp.status_code == 422

    def test_criar_usuario_senha_comum_retorna_422(self, client):
        """Senha da blocklist deve retornar 422."""
        resp = client.post("/usuarios", json={
            "nome": "Comum",
            "email": "comum@example.com",
            "senha": "password123"
        })
        assert resp.status_code == 422

    def test_resposta_nao_expoe_senha_hash(self, client):
        cur = MagicMock()
        cur.lastrowid = 7
        cur.rowcount = 1
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/usuarios", json={
                "nome": "Hash Test",
                "email": "hashtest@example.com",
                "senha": "SenhaForte1"
            })
        assert "senha_hash" not in resp.text
        assert "$2b$" not in resp.text


# =========================================================================== #
# Buscar usuario
# =========================================================================== #

class TestBuscarUsuario:
    def test_buscar_proprio_perfil(self, client_usuario):
        """GET /usuarios/me retorna perfil do usuario logado."""
        call_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchone.return_value = fake_usuario(id_usuario=1)
            c.rowcount = 1
            return c

        conn = MagicMock()
        conn.cursor.side_effect = cursor_factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/usuarios/me")

        assert resp.status_code == 200
        assert resp.json()["id_usuario"] == 1

    def test_buscar_usuario_por_id_retorna_perfil_publico(self, client_usuario):
        """GET /usuarios/{id} retorna perfil sem email."""
        call_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchone.return_value = {
                    "id_usuario": 2,
                    "nome": "Outro User",
                    "bio": None,
                    "foto_perfil": None,
                    "data_criacao": "2026-01-01",
                }
            c.rowcount = 1
            return c

        conn = MagicMock()
        conn.cursor.side_effect = cursor_factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/usuarios/2")

        assert resp.status_code == 200
        assert "email" not in resp.json()

    def test_buscar_usuario_nao_encontrado(self, client_usuario):
        """GET /usuarios/{id} para id inexistente retorna 404."""
        call_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchone.return_value = None
            c.rowcount = 0
            return c

        conn = MagicMock()
        conn.cursor.side_effect = cursor_factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/usuarios/9999")

        assert resp.status_code == 404


# =========================================================================== #
# Atualizar usuario
# =========================================================================== #

class TestAtualizarUsuario:
    def test_atualizar_proprio_perfil(self, client_usuario):
        """PUT /usuarios/1 com token id=1 deve funcionar."""
        call_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.fetchone.return_value = (1,)
            c.rowcount = 1
            return c

        conn = MagicMock()
        conn.cursor.side_effect = cursor_factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/usuarios/1", json={
                "nome": "Novo Nome",
                "email": "novo@example.com",
                "bio": "Nova bio"
            })

        assert resp.status_code == 200

    def test_nao_pode_atualizar_perfil_de_outro(self, client_usuario):
        """PUT /usuarios/2 com token id=1 retorna 403."""
        cur = MagicMock()
        cur.fetchone.return_value = (1,)
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/usuarios/2", json={
                "nome": "Nome",
                "email": "email@example.com"
            })

        assert resp.status_code == 403


# =========================================================================== #
# Deletar usuario
# =========================================================================== #

class TestDeletarUsuario:
    def test_deletar_proprio_usuario(self, client_usuario):
        """DELETE /usuarios/1 com token id=1 deve funcionar."""
        call_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.fetchone.return_value = (1,)
            c.rowcount = 1
            return c

        conn = MagicMock()
        conn.cursor.side_effect = cursor_factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/usuarios/1")

        assert resp.status_code == 200

    def test_nao_pode_deletar_outro_usuario(self, client_usuario):
        """DELETE /usuarios/2 com token id=1 retorna 403."""
        cur = MagicMock()
        cur.fetchone.return_value = (1,)
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/usuarios/2")

        assert resp.status_code == 403

    def test_deletar_sem_autenticacao_retorna_401(self, client):
        resp = client.delete("/usuarios/1")
        assert resp.status_code == 401
