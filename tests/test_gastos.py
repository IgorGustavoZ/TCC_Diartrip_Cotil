import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _criar_usuario_e_token(email: str, senha: str = "Senha@Forte123") -> tuple[dict, str]:
    payload = {"nome": "Usuário Teste Gastos", "email": email, "senha": senha}
    resp = client.post("/usuarios", json=payload)
    assert resp.status_code in (200, 201)
    usuario = resp.json()
    login = client.post("/login", json={"email": email, "senha": senha})
    token = login.json()["token"]
    return usuario, token


@pytest.fixture
def usuario_e_token():
    usuario, token = _criar_usuario_e_token("gastos_pytest@diartrip.com")
    yield usuario, token
    client.delete(
        f"/usuarios/{usuario['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.fixture
def grupo_criado(usuario_e_token):
    usuario, token = usuario_e_token
    payload = {
        "nome_grupo": "Viagem Teste Pytest",
        "destino_principal": "Rio de Janeiro",
        "data_inicio": "2025-07-01",
        "data_fim": "2025-07-10",
        "tipo_viagem": "lazer",
        "preferencias": "praia",
        "orcamento": 3000.00,
    }
    resp = client.post(
        "/grupos",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in (200, 201)
    grupo = resp.json()
    yield grupo, token
    client.delete(
        f"/grupos/{grupo['id_grupo']}",
        headers={"Authorization": f"Bearer {token}"},
    )


class TestCriarGasto:
    def test_membro_pode_criar_gasto(self, grupo_criado):
        grupo, token = grupo_criado
        payload = {"descricao": "Passagem aérea", "valor": 450.00, "categoria": "transporte"}
        resp = client.post(
            f"/grupos/{grupo['id_grupo']}/gastos",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (200, 201)
        assert "id" in resp.json()

    def test_nao_membro_nao_pode_criar_gasto(self, grupo_criado):
        grupo, _ = grupo_criado
        _, token_estranho = _criar_usuario_e_token("estranho_pytest@diartrip.com")
        payload = {"descricao": "Gasto indevido", "valor": 100.00, "categoria": "outro"}
        resp = client.post(
            f"/grupos/{grupo['id_grupo']}/gastos",
            json=payload,
            headers={"Authorization": f"Bearer {token_estranho}"},
        )
        assert resp.status_code == 403

    def test_sem_autenticacao_retorna_401(self, grupo_criado):
        grupo, _ = grupo_criado
        payload = {"descricao": "Gasto anônimo", "valor": 50.00, "categoria": "outro"}
        resp = client.post(f"/grupos/{grupo['id_grupo']}/gastos", json=payload)
        assert resp.status_code == 401

    def test_valor_negativo_e_invalido(self, grupo_criado):
        grupo, token = grupo_criado
        payload = {"descricao": "Valor inválido", "valor": -100.00, "categoria": "outro"}
        resp = client.post(
            f"/grupos/{grupo['id_grupo']}/gastos",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


class TestListarGastos:
    def test_membro_pode_listar_gastos(self, grupo_criado):
        grupo, token = grupo_criado
        resp = client.get(
            f"/grupos/{grupo['id_grupo']}/gastos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_nao_membro_nao_pode_listar_gastos(self, grupo_criado):
        grupo, _ = grupo_criado
        _, token_estranho = _criar_usuario_e_token("estranho2_pytest@diartrip.com")
        resp = client.get(
            f"/grupos/{grupo['id_grupo']}/gastos",
            headers={"Authorization": f"Bearer {token_estranho}"},
        )
        assert resp.status_code == 403


class TestDeletarGasto:
    def test_dono_pode_deletar_proprio_gasto(self, grupo_criado):
        grupo, token = grupo_criado
        gasto = client.post(
            f"/grupos/{grupo['id_grupo']}/gastos",
            json={"descricao": "Para deletar", "valor": 10.00, "categoria": "transporte"},
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        resp = client.delete(
            f"/gastos/{gasto['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (200, 204)

    def test_nao_dono_nao_pode_deletar_gasto(self, grupo_criado):
        grupo, token_dono = grupo_criado
        gasto = client.post(
            f"/grupos/{grupo['id_grupo']}/gastos",
            json={"descricao": "Gasto do dono", "valor": 20.00, "categoria": "transporte"},
            headers={"Authorization": f"Bearer {token_dono}"},
        ).json()
        _, token_estranho = _criar_usuario_e_token("estranho3_pytest@diartrip.com")
        resp = client.delete(
            f"/gastos/{gasto['id']}",
            headers={"Authorization": f"Bearer {token_estranho}"},
        )
        assert resp.status_code == 403
