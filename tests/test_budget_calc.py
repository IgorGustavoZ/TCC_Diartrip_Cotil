import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

_EMAIL = "teste_budget@diartrip.com"
_SENHA = "password123"


@pytest.fixture
def usuario_e_token():
    client.post("/usuarios", json={"nome": "Tester", "email": _EMAIL, "senha": _SENHA})
    login_resp = client.post("/login", json={"email": _EMAIL, "senha": _SENHA})
    dados = login_resp.json()
    token = dados["token"]
    usuario_id = dados["usuario_id"]
    yield usuario_id, token
    client.delete(f"/usuarios/{usuario_id}", headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def grupo_com_gastos(usuario_e_token):
    _, token = usuario_e_token
    headers = {"Authorization": f"Bearer {token}"}
    orcamento_inicial = 5000.00

    grupo_resp = client.post(
        "/grupos",
        json={
            "nome_grupo": "Teste Financeiro",
            "destino_principal": "Paris",
            "data_inicio": "2026-01-01",
            "data_fim": "2026-01-10",
            "orcamento": orcamento_inicial,
            "tipo_viagem": "Luxo",
            "preferencias": "Vinho",
        },
        headers=headers,
    )
    id_grupo = grupo_resp.json()["id_grupo"]

    gastos = [500.00, 750.50]
    for valor in gastos:
        client.post(
            f"/grupos/{id_grupo}/gastos",
            json={"valor": valor, "categoria": "Alimentação", "descricao": "Gasto teste"},
            headers=headers,
        )

    yield id_grupo, orcamento_inicial, gastos, token
    client.delete(f"/grupos/{id_grupo}", headers=headers)


def test_calculo_orcamento_dashboard(grupo_com_gastos):
    id_grupo, orcamento_inicial, gastos, token = grupo_com_gastos
    headers = {"Authorization": f"Bearer {token}"}

    dash_resp = client.get(f"/grupos/{id_grupo}/dashboard/geral", headers=headers)
    assert dash_resp.status_code == 200
    dados = dash_resp.json()

    total_esperado = sum(gastos)
    restante_esperado = orcamento_inicial - total_esperado

    assert dados["total_consumido"] == total_esperado
    assert dados["orcamento_restante"] == restante_esperado
