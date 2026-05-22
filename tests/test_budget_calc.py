import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

_EMAIL = "teste_budget@diartrip.com"
_SENHA = "Teste1234"


@pytest.fixture
def usuario_logado():
    client.post("/usuarios", json={"nome": "Tester", "email": _EMAIL, "senha": _SENHA})
    login_resp = client.post("/login", json={"email": _EMAIL, "senha": _SENHA})
    dados = login_resp.json()
    usuario_id = dados["usuario_id"]
    yield usuario_id
    client.delete(f"/usuarios/{usuario_id}")


@pytest.fixture
def grupo_com_gastos(usuario_logado):  # noqa: ARG001 — fixture usada como dependência
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
        }
    )
    id_grupo = grupo_resp.json()["id_grupo"]

    gastos = [500.00, 750.50]
    for valor in gastos:
        client.post(
            f"/grupos/{id_grupo}/gastos",
            json={"valor": valor, "categoria": "Alimentação", "descricao": "Gasto teste"}
        )

    yield id_grupo, orcamento_inicial, gastos
    client.delete(f"/grupos/{id_grupo}")


def test_calculo_orcamento_dashboard(grupo_com_gastos):
    id_grupo, orcamento_inicial, gastos = grupo_com_gastos

    dash_resp = client.get(f"/grupos/{id_grupo}/dashboard/geral")
    assert dash_resp.status_code == 200
    dados = dash_resp.json()

    total_esperado = sum(gastos)
    restante_esperado = orcamento_inicial - total_esperado

    assert dados["total_consumido"] == total_esperado
    assert dados["orcamento_restante"] == restante_esperado


def test_balanco_entre_membros(usuario_logado):
    # 1. Criar grupo
    grupo_resp = client.post(
        "/grupos",
        json={
            "nome_grupo": "Grupo Divisão",
            "destino_principal": "Tokio",
            "data_inicio": "2026-05-01",
            "data_fim": "2026-05-15",
            "orcamento": 10000,
            "tipo_viagem": "Anime",
            "preferencias": "Sushi",
        }
    )
    id_grupo = grupo_resp.json()["id_grupo"]

    # 2. Criar segundo usuário e entrar no grupo
    email2 = "outro@diartrip.com"
    client.post("/usuarios", json={"nome": "Outro", "email": email2, "senha": "Senha1234"})
    
    # Login como Outro para pegar o ID
    login2 = client.post("/login", json={"email": email2, "senha": "Senha1234"})
    id_outro = login2.json()["usuario_id"]
    
    # Entrar no grupo usando código de convite
    codigo = grupo_resp.json()["codigo_convite"]
    client.post("/grupos/entrar", json={"codigo_convite": codigo})

    # IMPORTANTE: Voltar a logar como o usuário principal (Tester) para pagar o gasto
    client.post("/login", json={"email": _EMAIL, "senha": _SENHA})

    # 3. Registrar gasto (usuário logado paga 100)
    # Pela nossa nova regra, se não passar id_usuarios_divisao, divide entre todos (Tester e Outro)
    resp_gasto = client.post(
        f"/grupos/{id_grupo}/gastos",
        json={
            "valor": 100.00, 
            "categoria": "Alimentação", 
            "descricao": "Divisão teste",
            "data_gasto": "2026-05-10"
        }
    )
    assert resp_gasto.status_code == 200

    # 4. Verificar balanço
    balanco_resp = client.get(f"/grupos/{id_grupo}/balanco")
    assert balanco_resp.status_code == 200
    balanco = balanco_resp.json()

    # Procura o usuário logado no balanço
    meu_balanco = None
    outro_balanco = None
    for m in balanco:
        if m["id_usuario"] == usuario_logado:
            meu_balanco = m
        if m["id_usuario"] == id_outro:
            outro_balanco = m

    assert meu_balanco is not None, "Meu usuário não apareceu no balanço"
    assert outro_balanco is not None, "O outro usuário não apareceu no balanço"

    # Eu paguei 100, dividiu 50 pra cada. Devo receber 50 dos outros.
    assert float(meu_balanco["a_receber"]) == 50.00
    assert float(meu_balanco["saldo"]) == 50.00
    
    # O outro deve pagar 50.
    assert float(outro_balanco["a_pagar"]) == 50.00
    assert float(outro_balanco["saldo"]) == -50.00

    # Limpeza
    client.delete(f"/grupos/{id_grupo}")
    client.post("/login", json={"email": email2, "senha": "Senha1234"})
    client.delete(f"/usuarios/{id_outro}")
    # Volta pro login original
    client.post("/login", json={"email": _EMAIL, "senha": _SENHA})
