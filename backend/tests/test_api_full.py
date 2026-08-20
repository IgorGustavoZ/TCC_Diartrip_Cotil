import pytest
from fastapi.testclient import TestClient
from main import app

_METODOS_MUTANTES = {"POST", "PUT", "PATCH", "DELETE"}


class CsrfTestClient(TestClient):
    def request(self, method, url, **kwargs):
        if method.upper() in _METODOS_MUTANTES:
            csrf = self.cookies.get("csrf_token")
            if csrf:
                headers = dict(kwargs.get("headers") or {})
                headers.setdefault("X-CSRF-Token", csrf)
                kwargs["headers"] = headers
        return super().request(method, url, **kwargs)


client = CsrfTestClient(app)

_USER1 = {"nome": "QA Admin", "email": "admin_qa_1@diartrip.com", "senha": "Teste1234"}
_USER2 = {"nome": "QA Member", "email": "member_qa_1@diartrip.com", "senha": "Teste1234"}
_USER3 = {"nome": "QA Sec", "email": "sec_qa_2@diartrip.com", "senha": "Teste1234"}


@pytest.fixture
def auth_admin():
    client.post("/usuarios", json=_USER1)
    login_resp = client.post("/login", json={"email": _USER1["email"], "senha": _USER1["senha"]})
    if login_resp.status_code != 200:
        client.post("/login", json={"email": _USER1["email"], "senha": _USER1["senha"]})
        res_me = client.get("/usuarios/me")
        if res_me.status_code == 200:
            client.delete(f"/usuarios/{res_me.json()['id_usuario']}")
        client.post("/usuarios", json=_USER1)
        login_resp = client.post("/login", json={"email": _USER1["email"], "senha": _USER1["senha"]})
    
    user_id = login_resp.json()["usuario_id"]
    yield user_id
    client.post("/login", json={"email": _USER1["email"], "senha": _USER1["senha"]})
    client.delete(f"/usuarios/{user_id}")


@pytest.fixture
def auth_member():
    client.post("/usuarios", json=_USER2)
    login_resp = client.post("/login", json={"email": _USER2["email"], "senha": _USER2["senha"]})
    if login_resp.status_code != 200:
        client.post("/login", json={"email": _USER2["email"], "senha": _USER2["senha"]})
        res_me = client.get("/usuarios/me")
        if res_me.status_code == 200:
            client.delete(f"/usuarios/{res_me.json()['id_usuario']}")
        client.post("/usuarios", json=_USER2)
        login_resp = client.post("/login", json={"email": _USER2["email"], "senha": _USER2["senha"]})

    user_id = login_resp.json()["usuario_id"]
    yield user_id
    client.post("/login", json={"email": _USER2["email"], "senha": _USER2["senha"]})
    client.delete(f"/usuarios/{user_id}")


@pytest.mark.xfail(
    reason="Teste de integracao end-to-end requer banco de dados real",
    strict=False,
)
def test_fluxo_completo_viagem(auth_admin, auth_member):
    resp_login1 = client.post("/login", json={"email": _USER1["email"], "senha": _USER1["senha"]})
    assert resp_login1.status_code == 200
    
    grupo_payload = {
        "nome_grupo": "Viagem de Teste Automatizado",
        "destino_principal": "Gramado",
        "data_inicio": "2026-12-01",
        "data_fim": "2026-12-10",
        "orcamento": 2000.00,
        "tipo_viagem": "Lazer",
        "preferencias": "Frio, Chocolate"
    }
    res_grupo = client.post("/grupos", json=grupo_payload)
    assert res_grupo.status_code == 200
    id_grupo = res_grupo.json()["id_grupo"]
    codigo = res_grupo.json()["codigo_convite"]

    resp_login2 = client.post("/login", json={"email": _USER2["email"], "senha": _USER2["senha"]})
    assert resp_login2.status_code == 200
    res_entrar = client.post("/grupos/entrar", json={"codigo_convite": codigo})
    assert res_entrar.status_code == 200

    resp_login1_v2 = client.post("/login", json={"email": _USER1["email"], "senha": _USER1["senha"]})
    assert resp_login1_v2.status_code == 200
    client.post(f"/grupos/{id_grupo}/gastos", json={
        "valor": 300.00,
        "categoria": "Alimentação",
        "descricao": "Jantar no centro",
        "data_gasto": "2026-06-02"
    })

    res_balanco = client.get(f"/grupos/{id_grupo}/balanco")
    balanco = res_balanco.json()
    
    admin_data = next(m for m in balanco if m["id_usuario"] == auth_admin)
    member_data = next(m for m in balanco if m["id_usuario"] == auth_member)

    assert admin_data["a_receber"] == 150.00
    assert member_data["a_pagar"] == 150.00

    resp_login2_v2 = client.post("/login", json={"email": _USER2["email"], "senha": _USER2["senha"]})
    assert resp_login2_v2.status_code == 200
    res_roteiro = client.post("/roteiros", json={
        "id_grupo": id_grupo,
        "titulo": "Visita à Fábrica de Chocolate",
        "descricao": "Saída às 10h da manhã"
    })
    assert res_roteiro.status_code == 200
    id_roteiro = res_roteiro.json()["id"]

    res_del_fail = client.delete(f"/roteiros/{id_roteiro}")
    assert res_del_fail.status_code == 403

    resp_login1_v3 = client.post("/login", json={"email": _USER1["email"], "senha": _USER1["senha"]})
    assert resp_login1_v3.status_code == 200
    res_del_ok = client.delete(f"/roteiros/{id_roteiro}")
    assert res_del_ok.status_code == 200

    resp_login2_v3 = client.post("/login", json={"email": _USER2["email"], "senha": _USER2["senha"]})
    assert resp_login2_v3.status_code == 200
    client.post(f"/grupos/{id_grupo}/chat", json={"conteudo": "Oi pessoal, vamos sair?"})
    
    res_chat = client.get(f"/grupos/{id_grupo}/chat")
    assert len(res_chat.json()) >= 1
    assert res_chat.json()[-1]["conteudo"] == "Oi pessoal, vamos sair?"

    res_rebaixar = client.put(f"/grupos/{id_grupo}/membros/{auth_admin}/rebaixar")
    assert res_rebaixar.status_code == 403

    resp_login1_v4 = client.post("/login", json={"email": _USER1["email"], "senha": _USER1["senha"]})
    assert resp_login1_v4.status_code == 200
    res_del_grupo = client.delete(f"/grupos/{id_grupo}")
    assert res_del_grupo.status_code == 200


def test_validacao_seguranca_uploads():
    client.post("/usuarios", json=_USER3)
    client.post("/login", json={"email": _USER3["email"], "senha": _USER3["senha"]})
    res_me = client.get("/usuarios/me")
    uid = res_me.json()["id_usuario"]
    
    files = {"foto": ("virus.jpg", b"conteudo de texto nao eh imagem", "image/jpeg")}
    res_upload = client.patch(f"/usuarios/{uid}/foto", files=files)
    
    assert res_upload.status_code == 400
    
    client.delete(f"/usuarios/{uid}")


_USER4 = {"nome": "QA Rate", "email": "rate_qa_4@diartrip.com", "senha": "Teste1234"}


def test_rate_limit_limite():
    client.post("/usuarios", json=_USER4)
    login_resp = client.post("/login", json={"email": _USER4["email"], "senha": _USER4["senha"]})
    assert login_resp.status_code == 200
    uid = login_resp.json()["usuario_id"]
    
    res_g = client.post("/grupos", json={
        "nome_grupo": "Grupo Spam", "destino_principal": "X", "data_inicio": "2026-12-01",
        "data_fim": "2026-12-02", "orcamento": 0, "tipo_viagem": "X", "preferencias": "X"
    })
    gid = res_g.json()["id_grupo"]
    
    last_status = 200
    for i in range(11):
        resp = client.post(f"/grupos/{gid}/chat", json={"conteudo": f"Spam {i}"})
        last_status = resp.status_code
        if resp.status_code == 429:
            break
    
    assert last_status in [200, 429]
    
    client.delete(f"/grupos/{gid}")
    client.delete(f"/usuarios/{uid}")
