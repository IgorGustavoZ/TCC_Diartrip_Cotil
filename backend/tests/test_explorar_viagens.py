from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db, make_connection


def _cur(fetchones=None, fetchalls=None, lastrowid=1, rowcount=1):
    cur = MagicMock()
    cur.lastrowid = lastrowid
    cur.rowcount = rowcount
    if fetchones is not None:
        cur.fetchone.side_effect = list(fetchones)
    if fetchalls is not None:
        cur.fetchall.side_effect = list(fetchalls)
    else:
        cur.fetchall.return_value = []
    return cur


class TestPublicarViagem:
    def test_admin_publica_viagem_com_limite_valido(self, client_admin):
        cur = _cur(fetchones=[(1,), {"cargo": "admin"}, {"total": 2}], rowcount=1)
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/grupos/10/publicar", json={"publica": True, "limite_participantes": 5})
        assert resp.status_code == 200

    def test_publicar_sem_limite_retorna_400(self, client_admin):
        cur = _cur(fetchones=[(1,), {"cargo": "admin"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/grupos/10/publicar", json={"publica": True})
        assert resp.status_code == 400

    def test_publicar_limite_menor_que_membros_atuais_retorna_400(self, client_admin):
        cur = _cur(fetchones=[(1,), {"cargo": "admin"}, {"total": 5}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/grupos/10/publicar", json={"publica": True, "limite_participantes": 3})
        assert resp.status_code == 400

    def test_admin_despublica_viagem(self, client_admin):
        cur = _cur(fetchones=[(1,), {"cargo": "admin"}], rowcount=1)
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/grupos/10/publicar", json={"publica": False})
        assert resp.status_code == 200

    def test_membro_comum_nao_pode_publicar(self, client_usuario):
        cur = _cur(fetchones=[(1,), {"cargo": "membro"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/grupos/10/publicar", json={"publica": True, "limite_participantes": 5})
        assert resp.status_code == 403

    def test_publicar_sem_autenticacao_retorna_401(self, client):
        resp = client.put("/grupos/10/publicar", json={"publica": False})
        assert resp.status_code == 401


class TestListarExplorar:
    def test_lista_viagens_publicas(self, client_usuario):
        viagem = {
            "id_grupo": 10, "nome_grupo": "Paris em Setembro", "destino_principal": "Paris",
            "data_inicio": "2026-09-10", "data_fim": "2026-09-20", "criador": "Igor",
            "limite_participantes": 5, "vagas_ocupadas": 3,
        }
        cur = _cur(fetchones=[(1,)], fetchalls=[[viagem]])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/explorar")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id_grupo"] == 10

    def test_busca_por_destino(self, client_usuario):
        cur = _cur(fetchones=[(1,)], fetchalls=[[]])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/explorar?destino=Paris")
        assert resp.status_code == 200

    def test_listar_explorar_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/explorar")
        assert resp.status_code == 401


class TestDetalharExplorar:
    def test_detalhe_encontrado(self, client_usuario):
        viagem = {
            "id_grupo": 10, "nome_grupo": "Paris em Setembro", "destino_principal": "Paris",
            "data_inicio": "2026-09-10", "data_fim": "2026-09-20", "criador": "Igor",
            "limite_participantes": 5, "vagas_ocupadas": 3,
        }
        cur = _cur(fetchones=[(1,), viagem])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/explorar/10")
        assert resp.status_code == 200
        assert resp.json()["id_grupo"] == 10

    def test_viagem_privada_ou_inexistente_retorna_404(self, client_usuario):
        cur = _cur(fetchones=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/explorar/999")
        assert resp.status_code == 404


class TestSolicitarParticipacao:
    def test_solicitar_participacao(self, client_usuario):
        cur = _cur(fetchones=[(1,), {"limite_participantes": 5}, None, None, {"total": 2}], lastrowid=42)
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/explorar/10/solicitar", json={"mensagem": "Adoraria ir!"})
        assert resp.status_code == 200
        assert resp.json()["id_solicitacao"] == 42

    def test_solicitar_viagem_nao_publica_retorna_404(self, client_usuario):
        cur = _cur(fetchones=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/explorar/999/solicitar", json={})
        assert resp.status_code == 404

    def test_solicitar_ja_sendo_membro_retorna_400(self, client_usuario):
        cur = _cur(fetchones=[(1,), {"limite_participantes": 5}, {"exists": 1}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/explorar/10/solicitar", json={})
        assert resp.status_code == 400

    def test_solicitar_com_pendente_ja_aberta_retorna_409(self, client_usuario):
        cur = _cur(fetchones=[(1,), {"limite_participantes": 5}, None, {"exists": 1}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/explorar/10/solicitar", json={})
        assert resp.status_code == 409

    def test_solicitar_viagem_lotada_retorna_409(self, client_usuario):
        cur = _cur(fetchones=[(1,), {"limite_participantes": 2}, None, None, {"total": 2}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/explorar/10/solicitar", json={})
        assert resp.status_code == 409

    def test_solicitar_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/explorar/10/solicitar", json={})
        assert resp.status_code == 401


class TestListarSolicitacoes:
    def test_admin_lista_solicitacoes_pendentes(self, client_admin):
        solicitacao = {
            "id_solicitacao": 1, "id_grupo": 10, "nome_grupo": "Grupo Teste",
            "id_usuario_solicitante": 2, "nome": "Outro Usuario", "foto_perfil": None,
            "mensagem": "Quero ir!", "status": "pendente", "data_solicitacao": "2026-06-01T10:00:00",
        }
        cur = _cur(fetchones=[(1,), {"cargo": "admin"}], fetchalls=[[solicitacao]])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.get("/grupos/10/solicitacoes")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_membro_comum_nao_pode_listar_solicitacoes(self, client_usuario):
        cur = _cur(fetchones=[(1,), {"cargo": "membro"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/solicitacoes")
        assert resp.status_code == 403


class TestAceitarSolicitacao:
    def test_admin_aceita_solicitacao_sem_limite(self, client_admin):
        cur = _cur(fetchones=[
            (1,),
            {"id_grupo": 10, "id_usuario_solicitante": 2, "status": "pendente"},
            {"cargo": "admin"},
            {"limite_participantes": None},
            None,
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/solicitacoes/1/aceitar")
        assert resp.status_code == 200

    def test_admin_aceita_solicitacao_com_vaga_disponivel(self, client_admin):
        cur = _cur(fetchones=[
            (1,),
            {"id_grupo": 10, "id_usuario_solicitante": 2, "status": "pendente"},
            {"cargo": "admin"},
            {"limite_participantes": 5},
            None,
            {"total": 2},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/solicitacoes/1/aceitar")
        assert resp.status_code == 200

    def test_aceitar_com_viagem_lotada_retorna_409(self, client_admin):
        cur = _cur(fetchones=[
            (1,),
            {"id_grupo": 10, "id_usuario_solicitante": 2, "status": "pendente"},
            {"cargo": "admin"},
            {"limite_participantes": 2},
            None,
            {"total": 2},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/solicitacoes/1/aceitar")
        assert resp.status_code == 409

    def test_nao_admin_nao_pode_aceitar(self, client_usuario):
        cur = _cur(fetchones=[
            (1,),
            {"id_grupo": 10, "id_usuario_solicitante": 2, "status": "pendente"},
            {"cargo": "membro"},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/solicitacoes/1/aceitar")
        assert resp.status_code == 403

    def test_solicitacao_inexistente_retorna_404(self, client_admin):
        cur = _cur(fetchones=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/solicitacoes/999/aceitar")
        assert resp.status_code == 404

    def test_solicitacao_ja_respondida_retorna_409(self, client_admin):
        cur = _cur(fetchones=[
            (1,),
            {"id_grupo": 10, "id_usuario_solicitante": 2, "status": "aceita"},
            {"cargo": "admin"},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/solicitacoes/1/aceitar")
        assert resp.status_code == 409


class TestRecusarSolicitacao:
    def test_admin_recusa_solicitacao(self, client_admin):
        cur = _cur(fetchones=[
            (1,),
            {"id_grupo": 10, "id_usuario_solicitante": 2, "status": "pendente"},
            {"cargo": "admin"},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/solicitacoes/1/recusar")
        assert resp.status_code == 200
