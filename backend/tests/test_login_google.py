"""test_login_google.py — Login/cadastro com Google (POST /google).

O token de identidade nunca é decodificado "na mão" aqui: toda validação de
assinatura/audiência/emissor/expiração é delegada à biblioteca oficial
google-auth (google.oauth2.id_token.verify_oauth2_token), então os testes
mockam essa função — exatamente o que a tarefa pede (nunca usar tokens reais
de usuários em testes automatizados).
"""
from unittest.mock import MagicMock, patch

import pytest
from mysql.connector import IntegrityError

from tests.conftest import make_cursor, make_connection, fake_get_db

_PATCH_VERIFY = "google.oauth2.id_token.verify_oauth2_token"


def _claims(**over):
    base = {
        "iss": "https://accounts.google.com",
        "sub": "google-sub-123456",
        "email": "novo.usuario@gmail.com",
        "email_verified": True,
        "name": "Fulano da Silva",
        "picture": "https://lh3.googleusercontent.com/a/foto123",
    }
    base.update(over)
    return base


class TestLoginGoogleUsuarioNovo:
    def test_token_valido_cria_conta_e_loga(self, client):
        cur = make_cursor(rows=[None, None], lastrowid=77)
        conn = make_connection(cur)
        with patch(_PATCH_VERIFY, return_value=_claims()), \
             patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/google", json={"credential": "token-falso"})
        assert resp.status_code == 200
        corpo = resp.json()
        assert corpo["usuario_id"] == 77
        assert "mensagem" in corpo
        assert "access_token" in resp.cookies

    def test_resposta_compativel_com_login_tradicional(self, client):
        # Mesmo response_model (LoginResponse) do /login — nunca expõe o
        # token do Google nem o JWT do Diartrip no corpo da resposta.
        cur = make_cursor(rows=[None, None], lastrowid=78)
        conn = make_connection(cur)
        with patch(_PATCH_VERIFY, return_value=_claims(sub="outro-sub")), \
             patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/google", json={"credential": "token-falso"})
        corpo = resp.json()
        assert set(corpo.keys()) == {"mensagem", "usuario_id"}
        assert "token-falso" not in resp.text
        assert "access_token" not in corpo


class TestLoginGoogleUsuarioExistente:
    def test_conta_ja_vinculada_apenas_loga(self, client):
        cur = make_cursor(rows=[{"id_usuario": 42}])
        conn = make_connection(cur)
        with patch(_PATCH_VERIFY, return_value=_claims()), \
             patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/google", json={"credential": "token-falso"})
        assert resp.status_code == 200
        assert resp.json()["usuario_id"] == 42

    def test_requisicoes_repetidas_nao_criam_usuarios_duplicados(self, client):
        claims = _claims(sub="sub-repetido")

        cur1 = make_cursor(rows=[None, None], lastrowid=90)
        conn1 = make_connection(cur1)
        with patch(_PATCH_VERIFY, return_value=claims), \
             patch("database.get_db", fake_get_db(conn1)):
            resp1 = client.post("/google", json={"credential": "token-1"})
        assert resp1.status_code == 200
        assert resp1.json()["usuario_id"] == 90

        # segunda chamada "repetida": agora a conta já existe (mesmo sub) —
        # o fluxo deve reconhecer e logar, nunca inserir de novo.
        cur2 = make_cursor(rows=[{"id_usuario": 90}])
        conn2 = make_connection(cur2)
        with patch(_PATCH_VERIFY, return_value=claims), \
             patch("database.get_db", fake_get_db(conn2)):
            resp2 = client.post("/google", json={"credential": "token-1"})
        assert resp2.status_code == 200
        assert resp2.json()["usuario_id"] == 90


class TestLoginGoogleEmailLocalSemVinculacao:
    def test_email_existente_nao_vinculado_retorna_409(self, client):
        cur = make_cursor(rows=[None, {"id_usuario": 5}])
        conn = make_connection(cur)
        with patch(_PATCH_VERIFY, return_value=_claims()), \
             patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/google", json={"credential": "token-falso"})
        assert resp.status_code == 409
        assert "senha" in resp.json()["detail"].lower()

    def test_email_existente_nao_cria_segunda_conta(self, client):
        cur = make_cursor(rows=[None, {"id_usuario": 5}])
        conn = make_connection(cur)
        with patch(_PATCH_VERIFY, return_value=_claims()), \
             patch("database.get_db", fake_get_db(conn)):
            client.post("/google", json={"credential": "token-falso"})
        execucoes = [c.args[0] for c in cur.execute.call_args_list]
        assert not any("INSERT" in e for e in execucoes)


class TestLoginGoogleTokenInvalido:
    def test_token_invalido_retorna_401(self, client):
        with patch(_PATCH_VERIFY, side_effect=ValueError("assinatura inválida")):
            resp = client.post("/google", json={"credential": "lixo"})
        assert resp.status_code == 401
        assert "inválid" in resp.json()["detail"].lower() or "expirad" in resp.json()["detail"].lower()

    def test_token_expirado_retorna_401(self, client):
        with patch(_PATCH_VERIFY, side_effect=ValueError("Token expired")):
            resp = client.post("/google", json={"credential": "expirado"})
        assert resp.status_code == 401

    def test_token_para_outro_client_id_retorna_401(self, client):
        # verify_oauth2_token já valida a audiência internamente — simulamos
        # a biblioteca rejeitando por audiência errada.
        with patch(_PATCH_VERIFY, side_effect=ValueError("Wrong audience")):
            resp = client.post("/google", json={"credential": "audiencia-errada"})
        assert resp.status_code == 401

    def test_email_nao_verificado_retorna_401(self, client):
        with patch(_PATCH_VERIFY, return_value=_claims(email_verified=False)):
            resp = client.post("/google", json={"credential": "nao-verificado"})
        assert resp.status_code == 401
        assert "verificad" in resp.json()["detail"].lower()

    def test_emissor_invalido_retorna_401(self, client):
        with patch(_PATCH_VERIFY, return_value=_claims(iss="https://outro-emissor.com")):
            resp = client.post("/google", json={"credential": "emissor-errado"})
        assert resp.status_code == 401

    def test_credential_ausente_retorna_422(self, client):
        resp = client.post("/google", json={})
        assert resp.status_code == 422

    def test_sem_client_id_configurado_retorna_503(self, client):
        with patch("routes.login.GOOGLE_CLIENT_ID", None):
            resp = client.post("/google", json={"credential": "qualquer"})
        assert resp.status_code == 503


class TestLoginGoogleFalhaDeConexao:
    def test_falha_no_banco_nao_vaza_detalhe_interno(self, client):
        def _get_db_que_falha():
            raise RuntimeError("conexão recusada pelo MySQL")

        with patch(_PATCH_VERIFY, return_value=_claims()), \
             patch("database.get_db", side_effect=_get_db_que_falha):
            resp = client.post("/google", json={"credential": "token-falso"})
        assert resp.status_code == 500
        assert "mysql" not in resp.text.lower()
        assert "conexão recusada" not in resp.text


class TestLoginGoogleCriacaoConcorrente:
    def test_corrida_na_criacao_reaproveita_conta_sem_duplicar(self, client):
        # Duas requisições quase simultâneas pro mesmo sub: a segunda bate
        # no UNIQUE de google_sub/email no INSERT — o código deve capturar
        # o IntegrityError (errno 1062) e reaproveitar a conta já criada
        # pela primeira, nunca estourar um erro pro usuário nem duplicar.
        fetch_idx = [0]
        fetchones = [None, None, {"id_usuario": 99}]

        def factory(**kw):
            c = MagicMock()

            def _fetchone():
                i = fetch_idx[0]
                fetch_idx[0] += 1
                return fetchones[i] if i < len(fetchones) else None

            def _execute(sql, params=None):
                if "INSERT INTO usuarios" in sql:
                    raise IntegrityError(msg="Duplicate entry", errno=1062)

            c.fetchone.side_effect = _fetchone
            c.fetchall.return_value = []
            c.execute.side_effect = _execute
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch(_PATCH_VERIFY, return_value=_claims()), \
             patch("database.get_db", fake_get_db(conn)):
            resp = client.post("/google", json={"credential": "token-corrida"})
        assert resp.status_code == 200
        assert resp.json()["usuario_id"] == 99
