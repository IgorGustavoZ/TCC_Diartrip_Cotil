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


class TestCriarGrupo:
    def test_criar_grupo_valido(self, client_usuario):
        conn = _conn_seq([(1,), None, None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos", json=GRUPO_PAYLOAD)
        assert resp.status_code == 201
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



class TestEntrarGrupo:
    def test_entrar_com_codigo_valido(self, client_usuario):
        conn = _conn_seq([
            (1,),
            {"id_grupo": 10, "nome_grupo": "Paris"},
            None,
            None,
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
            (1,),
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/entrar", json={"codigo_convite": "ABC123"})
        assert resp.status_code == 400



class TestAdminGrupo:
    def test_admin_pode_atualizar_grupo(self, client_admin):
        conn = _conn_seq([
            (99,),
            {"cargo": "admin"},
            {"cargo": "admin"},
            None,
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.put("/grupos/10", json=GRUPO_PAYLOAD)
        assert resp.status_code == 200

    def test_criador_pode_deletar_grupo(self, client_admin):
        # client_admin autentica como usuario_id=99, que aqui e o proprio criado_por.
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            c.lastrowid = 10
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)  # get_usuario_logado: usuario existe
            elif call_count[0] == 2:
                c.fetchone.return_value = (99,)  # criado_por
            else:
                c.fetchone.return_value = (1,)
                c.fetchall.return_value = []
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

    def test_deletar_grupo_apaga_dependencias_antes_do_grupo(self, client_admin):
        # Nao confia em ON DELETE CASCADE: o banco real tem gastos->grupos_viagem
        # como ON DELETE RESTRICT, entao o service precisa apagar explicitamente
        # os registros filhos antes do DELETE FROM grupos_viagem.
        call_count = [0]
        cursor_service = MagicMock()
        cursor_service.rowcount = 1
        cursor_service.fetchone.return_value = (99,)  # criado_por
        cursor_service.fetchall.return_value = []      # fotos

        def factory(**kw):
            call_count[0] += 1
            if call_count[0] == 1:
                c = MagicMock()
                c.fetchone.return_value = (1,)  # get_usuario_logado
                return c
            return cursor_service

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)), \
             patch("utils.cloudinary_upload.deletar_imagem", return_value=None):
            resp = client_admin.delete("/grupos/10")

        assert resp.status_code == 200
        sqls = [call.args[0] for call in cursor_service.execute.call_args_list]

        idx_gastos = next(i for i, s in enumerate(sqls) if s.strip().startswith("DELETE FROM gastos"))
        idx_divisao = next(i for i, s in enumerate(sqls) if "DELETE dg FROM divisao_gastos" in s)
        idx_grupo = next(i for i, s in enumerate(sqls) if s.strip().startswith("DELETE FROM grupos_viagem"))

        assert idx_divisao < idx_gastos < idx_grupo
        assert any("DELETE FROM grupo_membros" in s for s in sqls)
        assert any("DELETE FROM viagem_solicitacoes" in s for s in sqls)

    def test_admin_nao_criador_nao_pode_deletar_grupo(self, client_admin):
        # client_admin autentica como usuario_id=99, mas quem criou o grupo foi o usuario 1.
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)  # get_usuario_logado: usuario existe
            else:
                c.fetchone.return_value = (1,)  # criado_por = 1 (nao e' o usuario 99)
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.delete("/grupos/10")

        assert resp.status_code == 403

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


def _conn_sair(fetchones, cursors_out=None):
    """Como _conn_seq, mas guarda os cursores criados em cursors_out para
    inspecionar cursor.execute.call_args_list depois da chamada."""
    fetch_idx = [0]

    def factory(**kw):
        c = MagicMock()
        c.rowcount = 1

        def _fetchone():
            i = fetch_idx[0]
            fetch_idx[0] += 1
            return fetchones[i] if i < len(fetchones) else None

        c.fetchone.side_effect = _fetchone
        if cursors_out is not None:
            cursors_out.append(c)
        return c

    conn = MagicMock()
    conn.cursor.side_effect = factory
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


class TestSairGrupo:
    def test_membro_comum_pode_sair_e_orcamento_e_subtraido(self, client_usuario):
        cursors = []
        conn = _conn_sair([
            (1,),                                   # get_usuario_logado
            {"cargo": "membro"},                    # checar_membro_grupo
            {"criado_por": 2},                       # nao e' o criador
            {"cargo": "membro"},                     # _checar_ultimo_admin: nao e' admin
            {"orcamento": 2000},                     # orcamento do membro que sai
        ], cursors_out=cursors)

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/grupos/10/sair")

        assert resp.status_code == 200

        # a UPDATE de subtracao deve ter sido chamada com o orcamento do membro
        update_calls = [
            call for c in cursors for call in c.execute.call_args_list
            if "UPDATE grupos_viagem SET orcamento" in call.args[0]
        ]
        assert len(update_calls) == 1
        assert update_calls[0].args[1] == (2000, 10)

    def test_sair_sem_orcamento_nao_altera_orcamento_da_viagem(self, client_usuario):
        cursors = []
        conn = _conn_sair([
            (1,),
            {"cargo": "membro"},
            {"criado_por": 2},
            {"cargo": "membro"},
            {"orcamento": None},
        ], cursors_out=cursors)

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/grupos/10/sair")

        assert resp.status_code == 200
        assert not any(
            "UPDATE grupos_viagem SET orcamento" in call.args[0]
            for c in cursors for call in c.execute.call_args_list
        )

    def test_criador_nao_pode_sair(self, client_usuario):
        conn = _conn_sair([
            (1,),
            {"cargo": "admin"},
            {"criado_por": 1},  # o proprio usuario_id=1 e' o criador
        ])

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/grupos/10/sair")

        assert resp.status_code == 400


class TestListarMembros:
    def test_lista_retorna_foto_perfil(self, client_usuario):
        membros = [
            {"id_usuario": 1, "nome": "Igor", "foto_perfil": "https://res.cloudinary.com/x/igor.jpg", "cargo": "admin"},
            {"id_usuario": 2, "nome": "Maria", "foto_perfil": None, "cargo": "membro"},
        ]
        conn = _conn_seq([(1,), {"cargo": "membro"}], fetchalls={0: membros})
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/membros")

        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["foto_perfil"] == "https://res.cloudinary.com/x/igor.jpg"
        assert data[1]["foto_perfil"] is None
