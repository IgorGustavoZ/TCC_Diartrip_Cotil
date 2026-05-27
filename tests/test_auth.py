"""
test_auth.py — Testes de autenticacao e JWT.
"""
import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt as pyjwt
import pytest
import bcrypt

from tests.conftest import make_cursor, make_connection, fake_get_db

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"


def _make_login_db(senha_plain):
    hashed = bcrypt.hashpw(senha_plain.encode(), bcrypt.gensalt()).decode()
    cursor = make_cursor(rows=[{"id_usuario": 1, "senha_hash": hashed}])
    conn = make_connection(cursor)
    return conn, hashed


# =========================================================================== #
# Login
# =========================================================================== #

class TestLogin:
    def test_login_valido_seta_cookie(self, client):
        """Login valido seta cookie access_token."""
        senha = "SenhaForte1"
        conn, _ = _make_login_db(senha)
        with patch("database._pool.get_connection", return_value=conn):
            resp = client.post("/login", json={"email": "t@t.com", "senha": senha})
        assert resp.status_code == 200
        assert "access_token" in resp.cookies


    def test_login_valido_retorna_usuario_id(self, client):
        """Resposta do login deve conter usuario_id."""
        senha = "SenhaForte1"
        conn, _ = _make_login_db(senha)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/login", json={"email": "t@t.com", "senha": senha})
        assert resp.status_code == 200
        assert "usuario_id" in resp.json()

    def test_login_senha_errada_retorna_401(self, client):
        conn, _ = _make_login_db("SenhaCorreta1")
        with patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/login", json={"email": "t@t.com", "senha": "SenhaErrada1"})
        assert resp.status_code == 401

    def test_login_usuario_inexistente_retorna_401(self, client):
        cursor = make_cursor(rows=[])
        cursor.fetchone.side_effect = None
        cursor.fetchone.return_value = None
        conn = make_connection(cursor)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/login", json={"email": "nx@t.com", "senha": "Senha1"})
        assert resp.status_code == 401

    def test_login_mensagem_generica(self, client):
        """Mensagem de erro nao indica qual campo esta errado."""
        cursor = make_cursor(rows=[])
        cursor.fetchone.return_value = None
        conn = make_connection(cursor)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/login", json={"email": "x@x.com", "senha": "Qualquer1"})
        assert resp.status_code == 401
        detail = resp.json().get("detail", "").lower()
        assert "inv" in detail or "informac" in detail

    def test_login_nao_retorna_senha_hash(self, client):
        senha = "SenhaForte1"
        conn, hash_real = _make_login_db(senha)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/login", json={"email": "t@t.com", "senha": senha})
        assert hash_real not in resp.text
        assert "senha_hash" not in resp.text

    def test_logout_retorna_200(self, client_usuario):
        resp = client_usuario.post("/logout")
        assert resp.status_code == 200


# =========================================================================== #
# JWT — validacoes de token
# =========================================================================== #

class TestTokenJWT:
    def test_token_expirado_retorna_401(self, client):
        from fastapi.testclient import TestClient
        from main import app
        token = pyjwt.encode(
            {"id": 1, "jti": "exp-jti",
             "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            SECRET_KEY, algorithm=ALGORITHM,
        )
        with TestClient(app, raise_server_exceptions=False) as c:
            c.cookies.set("access_token", token)
            resp = c.get("/usuarios/me")
        assert resp.status_code == 401

    def test_token_assinatura_adulterada_retorna_401(self, client):
        from fastapi.testclient import TestClient
        from main import app
        token = pyjwt.encode(
            {"id": 1, "jti": "tamper",
             "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "chave-errada", algorithm=ALGORITHM,
        )
        with TestClient(app, raise_server_exceptions=False) as c:
            c.cookies.set("access_token", token)
            resp = c.get("/grupos")
        assert resp.status_code == 401

    def test_sem_token_retorna_401(self, client):
        resp = client.get("/usuarios/me")
        assert resp.status_code == 401

    def test_token_formato_invalido(self, client):
        from fastapi.testclient import TestClient
        from main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            c.cookies.set("access_token", "nao-e-um-jwt")
            resp = c.get("/grupos")
        assert resp.status_code == 401

    def test_rota_protegida_sem_token_retorna_401(self, client):
        resp = client.get("/grupos")
        assert resp.status_code == 401

    def test_token_algoritmo_none_rejeitado(self, client):
        import base64
        from fastapi.testclient import TestClient
        from main import app
        header = base64.urlsafe_b64encode(
            b'{"alg":"none","typ":"JWT"}'
        ).rstrip(b"=").decode()
        payload_enc = base64.urlsafe_b64encode(
            f'{{"id":1,"jti":"none","exp":{int(time.time()) + 3600}}}'.encode()
        ).rstrip(b"=").decode()
        token_none = f"{header}.{payload_enc}."
        with TestClient(app, raise_server_exceptions=False) as c:
            c.cookies.set("access_token", token_none)
            resp = c.get("/usuarios/me")
        assert resp.status_code == 401


# =========================================================================== #
# Seguranca de senhas
# =========================================================================== #

class TestSenhaSeguranca:
    def test_hash_bcrypt_nao_e_plaintext(self):
        from utils.security import gerar_hash
        h = gerar_hash("SenhaForte1")
        assert h != "SenhaForte1"
        assert h.startswith("$2b$") or h.startswith("$2a$")

    def test_verificar_senha_correta(self):
        from utils.security import gerar_hash, verificar_senha
        senha = "SenhaForte1"
        h = gerar_hash(senha)
        assert verificar_senha(senha, h) is True

    def test_verificar_senha_errada(self):
        from utils.security import gerar_hash, verificar_senha
        h = gerar_hash("SenhaCorreta1")
        assert verificar_senha("SenhaErrada1", h) is False

    def test_criar_e_decodificar_token(self):
        from utils.security import criar_token, decodificar_token
        uid = 42
        assert decodificar_token(criar_token(uid)) == uid

    def test_decodificar_token_expirado_lanca_401(self):
        from utils.security import decodificar_token
        from fastapi import HTTPException
        token = pyjwt.encode(
            {"id": 1, "jti": "exp3",
             "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
            SECRET_KEY, algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            decodificar_token(token)
        assert exc.value.status_code == 401

    def test_decodificar_token_assinatura_invalida_lanca_401(self):
        from utils.security import decodificar_token
        from fastapi import HTTPException
        token = pyjwt.encode(
            {"id": 1, "jti": "bad",
             "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "chave-errada", algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            decodificar_token(token)
        assert exc.value.status_code == 401


# =========================================================================== #
# Escalada de privilegio
# =========================================================================== #

class TestEscaladaPrivilegio:
    def test_usuario_nao_pode_deletar_outro_usuario(self, client_usuario):
        """Token de usuario_id=1 nao pode deletar usuario_id=2."""
        cur = MagicMock()
        cur.fetchone.return_value = (1,)
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/usuarios/2")
        assert resp.status_code == 403

    def test_membro_nao_pode_deletar_grupo(self, client_usuario):
        """Membro simples (cargo=membro) nao pode deletar grupo."""
        call_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchone.return_value = {"cargo": "membro"}
            c.rowcount = 1
            return c

        conn = MagicMock()
        conn.cursor.side_effect = cursor_factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/grupos/10")
        assert resp.status_code == 403

    def test_membro_nao_pode_atualizar_grupo(self, client_usuario):
        """Membro nao pode PUT /grupos/{id}."""
        call_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchone.return_value = {"cargo": "membro"}
            c.rowcount = 1
            return c

        conn = MagicMock()
        conn.cursor.side_effect = cursor_factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        dados = {
            "nome_grupo": "Novo", "destino_principal": "Roma",
            "data_inicio": "2026-07-01", "data_fim": "2026-07-15",
            "orcamento": 3000, "tipo_viagem": "aventura", "preferencias": "montanhas"
        }
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/grupos/10", json=dados)
        assert resp.status_code == 403
