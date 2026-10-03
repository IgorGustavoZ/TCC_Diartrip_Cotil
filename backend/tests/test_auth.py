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
    cursor = make_cursor(rows=[{"id_usuario": 1, "senha_hash": hashed, "email_verificado": 1}])
    conn = make_connection(cursor)
    return conn, hashed



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

    def test_login_email_nao_verificado_bloqueia_sessao(self, client):
        senha = "SenhaForte1"
        hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
        cursor = make_cursor(rows=[{
            "id_usuario": 1,
            "senha_hash": hashed,
            "email_verificado": 0,
        }])
        conn = make_connection(cursor)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/login", json={"email": "pendente@example.com", "senha": senha})
        assert resp.status_code == 403
        assert "access_token" not in resp.cookies

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



class TestTokenJWTExpiry:
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


def _hash_codigo_teste(codigo: str) -> str:
    import hashlib
    import hmac
    return hmac.new(SECRET_KEY.encode(), codigo.encode("ascii"), hashlib.sha256).hexdigest()


_SENHA_CADASTRO = "SenhaForte1"
_SENHA_CADASTRO_HASH = bcrypt.hashpw(_SENHA_CADASTRO.encode(), bcrypt.gensalt(4)).decode()


def _usuario_pendente(**extra):
    linha = {
        "id_usuario": 7,
        "senha_hash": _SENHA_CADASTRO_HASH,
        "email_verificado": 0,
        "codigo_verificacao_hash": _hash_codigo_teste("123456"),
        "codigo_verificacao_expira": datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10),
        "tentativas_verificacao": 0,
    }
    linha.update(extra)
    return linha


class TestVerificacaoEmail:
    def test_codigo_e_senha_validos_marcam_email_verificado(self):
        from services.email_verification_service import verificar_codigo

        cursor = make_cursor(rows=[_usuario_pendente()])
        conn = make_connection(cursor)
        with patch("services.email_verification_service.get_db", fake_get_db(conn)):
            resultado = verificar_codigo("Novo@Example.com", "123456", _SENHA_CADASTRO)

        assert resultado["usuario_id"] == 7
        assert cursor.execute.call_args_list[0].args[1] == ("novo@example.com",)
        assert cursor.execute.call_count == 2
        assert "email_verificado=1" in cursor.execute.call_args_list[1].args[0]

    def test_codigo_certo_com_senha_errada_e_rejeitado(self):
        """Quem tem só o código (dono da caixa) não ativa uma conta cadastrada
        por outra pessoa com senha que ele não conhece."""
        from fastapi import HTTPException
        from services.email_verification_service import verificar_codigo

        cursor = make_cursor(rows=[_usuario_pendente()])
        conn = make_connection(cursor)
        with patch("services.email_verification_service.get_db", fake_get_db(conn)):
            with pytest.raises(HTTPException) as exc:
                verificar_codigo("novo@example.com", "123456", "OutraSenha1")

        assert exc.value.status_code == 400
        assert cursor.execute.call_args_list[1].args[1] == (1, 7)  # conta como tentativa

    def test_email_ja_verificado_nao_revela_conta(self):
        from fastapi import HTTPException
        from services.email_verification_service import verificar_codigo

        cursor = make_cursor(rows=[_usuario_pendente(email_verificado=1)])
        conn = make_connection(cursor)
        with patch("services.email_verification_service.get_db", fake_get_db(conn)):
            with pytest.raises(HTTPException) as exc:
                verificar_codigo("ja@example.com", "000000", "qualquer")

        assert exc.value.status_code == 400
        assert exc.value.detail == "Codigo invalido"

    def test_codigo_expirado_e_rejeitado(self):
        from fastapi import HTTPException
        from services.email_verification_service import verificar_codigo

        cursor = make_cursor(rows=[_usuario_pendente(
            codigo_verificacao_expira=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1),
        )])
        conn = make_connection(cursor)
        with patch("services.email_verification_service.get_db", fake_get_db(conn)):
            with pytest.raises(HTTPException) as exc:
                verificar_codigo("novo@example.com", "123456", _SENHA_CADASTRO)

        assert exc.value.status_code == 400
        assert "expirado" in exc.value.detail.lower()
        assert cursor.execute.call_count == 2

    def test_codigo_invalido_incrementa_tentativas(self):
        from fastapi import HTTPException
        from services.email_verification_service import verificar_codigo

        cursor = make_cursor(rows=[_usuario_pendente(tentativas_verificacao=1)])
        conn = make_connection(cursor)
        with patch("services.email_verification_service.get_db", fake_get_db(conn)):
            with pytest.raises(HTTPException) as exc:
                verificar_codigo("novo@example.com", "654321", _SENHA_CADASTRO)

        assert exc.value.status_code == 400
        assert cursor.execute.call_args_list[1].args[1] == (2, 7)

    def test_rate_limit_ignora_maiusculas_do_email(self, client):
        """Variar maiúsculas não pode gerar contadores de rate limit novos."""
        with patch("services.email_verification_service.reenviar_codigo"):
            primeira = client.post("/usuarios/reenviar-codigo", json={"email": "caso@example.com"})
            segunda = client.post("/usuarios/reenviar-codigo", json={"email": "CASO@example.com"})
        assert primeira.status_code == 200
        assert segunda.status_code == 429


class TestTrocaEmail:
    def test_confirmar_troca_aplica_email_pendente(self):
        from services.email_verification_service import confirmar_troca_email

        cursor = make_cursor(rows=[_usuario_pendente(email_verificado=1, email_pendente="novo@example.com")])
        conn = make_connection(cursor)
        with patch("services.email_verification_service.get_db", fake_get_db(conn)):
            confirmar_troca_email(7, "123456")

        assert "email=email_pendente" in cursor.execute.call_args_list[1].args[0]

    def test_confirmar_sem_troca_pendente_retorna_400(self):
        from fastapi import HTTPException
        from services.email_verification_service import confirmar_troca_email

        cursor = make_cursor(rows=[_usuario_pendente(email_verificado=1, email_pendente=None)])
        conn = make_connection(cursor)
        with patch("services.email_verification_service.get_db", fake_get_db(conn)):
            with pytest.raises(HTTPException) as exc:
                confirmar_troca_email(7, "123456")
        assert exc.value.status_code == 400


class TestTokenJWT:
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
        """Quem nao e' o criador do grupo (mesmo sendo membro) nao pode deletar."""
        call_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchone.return_value = (2,)  # criado_por = 2, cliente e' o usuario 1
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
        """Quem nao e' o criador do grupo (mesmo sendo membro) nao pode editar."""
        call_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchone.return_value = {"criado_por": 2}  # cliente e' o usuario 1
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
            "tipo_viagem": "aventura", "preferencias": "montanhas"
        }
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/grupos/10", json=dados)
        assert resp.status_code == 403
