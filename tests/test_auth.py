import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def usuario_payload():
    return {
        "nome": "Teste Automatizado",
        "email": "teste_pytest@diartrip.com",
        "senha": "Senha@Forte123",
    }


@pytest.fixture
def usuario_criado(usuario_payload):
    """Cria um usuário e retorna seus dados. Remove após o teste."""
    resp = client.post("/usuarios", json=usuario_payload)
    assert resp.status_code in (200, 201), f"Falha ao criar usuário: {resp.text}"
    yield resp.json()
    token = _obter_token(usuario_payload["email"], usuario_payload["senha"])
    id_usuario = resp.json().get("id")
    if id_usuario and token:
        client.delete(
            f"/usuarios/{id_usuario}",
            headers={"Authorization": f"Bearer {token}"},
        )


def _obter_token(email: str, senha: str) -> str | None:
    resp = client.post("/login", json={"email": email, "senha": senha})
    if resp.status_code == 200:
        return resp.json().get("token")
    return None

class TestCriarUsuario:
    def test_cria_usuario_com_sucesso(self, usuario_payload, usuario_criado):
        assert usuario_criado.get("email") == usuario_payload["email"]

    def test_nao_permite_email_duplicado(self, usuario_payload, usuario_criado):
        resp = client.post("/usuarios", json=usuario_payload)
        assert resp.status_code == 409, "Deveria retornar 409 para email duplicado"

    def test_rejeita_payload_invalido(self):
        resp = client.post("/usuarios", json={"nome": "Sem email"})
        assert resp.status_code == 422

class TestLogin:
    def test_login_com_credenciais_corretas(self, usuario_payload, usuario_criado):
        resp = client.post(
            "/login",
            json={"email": usuario_payload["email"], "senha": usuario_payload["senha"]},
        )
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_login_com_senha_errada(self, usuario_payload, usuario_criado):
        resp = client.post(
            "/login",
            json={"email": usuario_payload["email"], "senha": "senhaErrada!"},
        )
        assert resp.status_code == 401

    def test_login_com_email_inexistente(self):
        resp = client.post(
            "/login",
            json={"email": "naoexiste@diartrip.com", "senha": "qualquer"},
        )
        assert resp.status_code == 401

class TestRotasProtegidas:
    def test_rota_sem_token_retorna_401(self):
        resp = client.get("/usuarios/me")
        assert resp.status_code == 401

    def test_rota_com_token_valido_retorna_200(self, usuario_payload, usuario_criado):
        token = _obter_token(usuario_payload["email"], usuario_payload["senha"])
        assert token is not None, "Token não obtido"
        resp = client.get("/usuarios/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_rota_com_token_invalido_retorna_401(self):
        resp = client.get("/usuarios/me", headers={"Authorization": "Bearer token_falso"})
        assert resp.status_code == 401