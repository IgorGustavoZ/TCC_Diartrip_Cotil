"""
test_grupos.py — Testes de grupos de viagem com banco mockado.
"""
from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db, fake_grupo

GRUPO_PAYLOAD = {
    "nome_grupo": "Viagem Paris",
    "destino_principal": "Paris",
    "data_inicio": "2026-06-01",
    "data_fim": "2026-06-15",
    "orcamento": 5000.0,
    "tipo_viagem": "lazer",
    "preferencias": "museus e gastronomia"
}


def _conn_seq(fetchones, fetchalls=None):
    """Gera conn mock com sequencia de retornos."""
    fa = fetchalls or {}
    fetch_idx = [0]
    fetchall_idx = [0]

    def factory(**kw):
        c = MagicMock()
        c.rowcount = 1
        c.lastrowid = 10

        def _fetchone():
            i = fetch_idx[0]
            fetch_idx[0] += 1
            return fetchones[i] if i < len(fetchones) else None

        def _fetchall():
            i = fetchall_idx[0]
            fetchall_idx[0] += 1
            return fa.get(i, [])

        c.fetchone.side_effect = _fetchone
        c.fetchall.side_effect = _fetchall
        return c

    conn = MagicMock()
    conn.cursor.side_effect = factory
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


# =========================================================================== #
# Criar grupo
# =========================================================================== #

class TestCriarGrupo:
    def test_criar_grupo_valido(self, client_usuario):
        conn = _conn_seq([(1,), None, None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos", json=GRUPO_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert "id_grupo" in data or "mensagem" in data

    def test_criar_grupo_data_fim_antes_inicio_retorna_422(self, client_usuario):
        payload = dict(GRUPO_PAYLOAD, data_fim="2026-05-01")
        resp = client_usuario.post("/grupos", json=payload)
        assert resp.status_code == 422

    def test_criar_grupo_orcamento_negativo_retorna_422(self, client_usuario):
        payload = dict(GRUPO_PAYLOAD, orcamento=-100.0)
        resp = client_usuario.post("/grupos", json=payload)
        assert resp.status_code == 422

    def test_criar_grupo_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/grupos", json=GRUPO_PAYLOAD)
        assert resp.status_code == 401


# =========================================================================== #
# Listar grupos
# =========================================================================== #

class TestListarGrupos:
    def test_listar_grupos_do_usuario(self, client_usuario):
        grupos = [fake_grupo(id_grupo=1), fake_grupo(id_grupo=2)]
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
                c.fetchall.return_value = []
            else:
                c.fetchone.return_value = None
                c.fetchall.return_value = grupos
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_listar_grupos_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/grupos")
        assert resp.status_code == 401


# =========================================================================== #
# Buscar grupo por ID
# =========================================================================== #

class TestBuscarGrupo:
    def test_membro_pode_buscar_grupo(self, client_usuario):
        grupo = fake_grupo(id_grupo=10)
        conn = _conn_seq([(1,), {"cargo": "membro"}, grupo])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10")
        assert resp.status_code == 200

    def test_nao_membro_recebe_403(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10")
        assert resp.status_code == 403


# =========================================================================== #
# Entrar por codigo de convite
# =========================================================================== #

class TestEntrarGrupo:
    def test_entrar_com_codigo_valido(self, client_usuario):
        conn = _conn_seq([
            (1,),                                       # auth
            {"id_grupo": 10, "nome_grupo": "Paris"},   # SELECT grupo
            None,                                       # ja e membro? Nao
            None,                                       # INSERT
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/entrar", json={"codigo_convite": "ABC123"})
        assert resp.status_code == 200

    def test_entrar_com_codigo_invalido_retorna_404(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/entrar", json={"codigo_convite": "XXXXXX"})
        assert resp.status_code == 404

    def test_entrar_em_grupo_ja_membro_retorna_400(self, client_usuario):
        conn = _conn_seq([
            (1,),
            {"id_grupo": 10, "nome_grupo": "Grupo"},
            (1,),   # ja e membro
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/entrar", json={"codigo_convite": "ABC123"})
        assert resp.status_code == 400


# =========================================================================== #
# Atualizar e deletar grupo (somente admin)
# =========================================================================== #

class TestAdminGrupo:
    def test_admin_pode_atualizar_grupo(self, client_admin):
        conn = _conn_seq([
            (99,),              # auth
            {"cargo": "admin"}, # verificar_pertence_ao_grupo
            {"cargo": "admin"}, # verificar_admin_do_grupo (encadeado)
            None,               # UPDATE
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/grupos/10", json=GRUPO_PAYLOAD)
        assert resp.status_code == 200

    def test_admin_pode_deletar_grupo(self, client_admin):
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            c.lastrowid = 10
            if call_count[0] == 1:
                c.fetchone.return_value = (99,)
            elif call_count[0] == 2:
                c.fetchone.return_value = {"cargo": "admin"}
            else:
                c.fetchone.return_value = (1,)
                c.fetchall.return_value = []   # sem fotos
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)), \
             patch("utils.cloudinary_upload.deletar_imagem", return_value=None):
            resp = client_admin.delete("/grupos/10")

        assert resp.status_code == 200

    def test_paginacao_busca_por_nome(self, client_usuario):
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchall.return_value = [fake_grupo()]
                c.fetchone.return_value = None
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/buscar?nome=Paris&limite=10&offset=0")

        assert resp.status_code == 200
