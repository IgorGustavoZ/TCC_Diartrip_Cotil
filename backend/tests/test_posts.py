from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db, fake_post, JPEG_MAGIC


def _conn_seq(fetchones):
    call_count = [0]

    def factory(**kw):
        call_count[0] += 1
        idx = call_count[0] - 1
        c = MagicMock()
        c.rowcount = 1
        c.lastrowid = 1
        c.fetchone.return_value = fetchones[idx] if idx < len(fetchones) else None
        c.fetchall.return_value = []
        return c

    conn = MagicMock()
    conn.cursor.side_effect = factory
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


class TestCriarPost:
    def test_criar_post_texto_simples(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "Minha primeira viagem!"})
        assert resp.status_code == 201
        data = resp.json()
        assert "id_post" in data or "mensagem" in data

    def test_criar_post_com_imagem_valida(self, client_usuario):
        conn = _conn_seq([(1,), None])
        fake_url = "https://res.cloudinary.com/test/image/upload/v1/abc.jpg"

        with patch("database.get_db", fake_get_db(conn)), \
             patch("utils.cloudinary_upload.upload_imagem", return_value=fake_url), \
             patch("services.post_service.strip_exif", side_effect=lambda b, e: b), \
             patch("utils.imagem_utils._validar_dimensoes"):
            resp = client_usuario.post(
                "/posts",
                data={"conteudo": "Com foto!"},
                files={"imagem": ("foto.jpg", JPEG_MAGIC, "image/jpeg")},
            )

        assert resp.status_code == 201

    def test_criar_post_vazio_sem_imagem_retorna_400(self, client_usuario):
        conn = _conn_seq([(1,)])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "   "})
        assert resp.status_code == 400

    def test_criar_post_apenas_imagem_retorna_201(self, client_usuario):
        conn = _conn_seq([(1,), None])
        fake_url = "https://res.cloudinary.com/test/image/upload/v1/abc.jpg"
        with patch("database.get_db", fake_get_db(conn)), \
             patch("utils.cloudinary_upload.upload_imagem", return_value=fake_url), \
             patch("services.post_service.strip_exif", side_effect=lambda b, e: b), \
             patch("utils.imagem_utils._validar_dimensoes"):
            resp = client_usuario.post(
                "/posts",
                data={"conteudo": ""},
                files={"imagem": ("foto.jpg", JPEG_MAGIC, "image/jpeg")},
            )
        assert resp.status_code == 201

    def test_criar_post_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/posts", data={"conteudo": "teste"})
        assert resp.status_code == 401

    def test_criar_post_conteudo_muito_longo_retorna_422(self, client_usuario):
        conn = _conn_seq([(1,)])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "A" * 5001})
        assert resp.status_code == 422


class TestListarPosts:
    def test_listar_todos_os_posts(self, client_usuario):
        posts = [fake_post(1), fake_post(2)]
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchall.return_value = posts
                c.fetchone.return_value = None
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/posts")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_listar_posts_do_usuario(self, client_usuario):
        posts = [fake_post(1, id_usuario=2)]
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            c.rowcount = 1
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchall.return_value = posts
                c.fetchone.return_value = None
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/posts/usuario/2")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_listar_posts_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/posts")
        assert resp.status_code == 401


def _por_bloco(fetch_por_bloco):
    """Cada `with get_db()` abre seu próprio cursor — aqui cada item da lista
    vira a sequência de fetchone() DAQUELE cursor (curtir()/comentar() reusam
    um único cursor pra várias consultas, diferente de _conn_seq acima, que
    dá um valor fixo por cursor)."""
    blocos = list(fetch_por_bloco)

    def factory(**kw):
        c = MagicMock()
        c.rowcount = 1
        c.lastrowid = 1
        valores = blocos.pop(0) if blocos else []
        c.fetchone.side_effect = list(valores) + [None] * 5
        c.fetchall.return_value = []
        return c

    conn = MagicMock()
    conn.cursor.side_effect = factory
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


class TestMiniFeedDoGrupo:
    def test_membro_pode_criar_post_no_grupo(self, client_usuario):
        # get_usuario_logado -> (1,); checar_membro_grupo (dentro de criar()) -> membro; INSERT -> None
        conn = _conn_seq([(1,), {"cargo": "membro"}, None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "Chegamos em Tóquio!", "id_grupo": 10})
        assert resp.status_code == 201

    def test_nao_membro_nao_pode_criar_post_no_grupo(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "Intruso", "id_grupo": 10})
        assert resp.status_code == 403

    def test_membro_pode_listar_posts_do_grupo(self, client_usuario):
        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            elif call_count[0] == 2:
                c.fetchone.return_value = {"cargo": "membro"}
                c.fetchall.return_value = [fake_post(1)]
            else:
                c.fetchone.return_value = None
                c.fetchall.return_value = []
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/posts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_nao_membro_nao_pode_listar_posts_do_grupo(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/posts")
        assert resp.status_code == 403

    def test_feed_global_nao_inclui_posts_de_grupo(self, client_usuario):
        cur = MagicMock()
        cur.fetchone.side_effect = [(1,), None]
        cur.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value = cur
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/posts")
        assert resp.status_code == 200
        select_call = next(c for c in cur.execute.call_args_list if "FROM posts" in c.args[0])
        assert "p.id_grupo IS NULL" in select_call.args[0]

    def test_curtir_post_de_grupo_exige_ser_membro(self, client_usuario):
        conn = _por_bloco([[(1,)], [{"id_grupo": 10}, None]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts/1/curtir")
        assert resp.status_code == 403

    def test_membro_pode_curtir_post_do_proprio_grupo(self, client_usuario):
        conn = _por_bloco([[(1,)], [{"id_grupo": 10}, {"cargo": "membro"}, None, {"total": 1}]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts/1/curtir")
        assert resp.status_code == 200

    def test_comentar_post_de_grupo_exige_ser_membro(self, client_usuario):
        conn = _por_bloco([[(1,)], [{"id_grupo": 10}, None]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts/1/comentar", json={"conteudo": "Que demais!"})
        assert resp.status_code == 403

    def test_curtir_post_do_feed_global_nao_exige_grupo(self, client_usuario):
        # post sem id_grupo/id_comunidade (feed global): qualquer usuario
        # logado curte, sem checar_membro_grupo/checar_membro_comunidade
        conn = _por_bloco([[(1,)], [{"id_grupo": None, "id_comunidade": None}, None, {"total": 1}]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts/1/curtir")
        assert resp.status_code == 200


class TestDeletarPost:
    def test_dono_pode_deletar_proprio_post(self, client_usuario):
        conn = _conn_seq([(1,), (1, None), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/posts/1")
        assert resp.status_code == 200

    def test_outro_usuario_nao_pode_deletar_post(self, client_usuario):
        conn = _conn_seq([(1,), (2, None)])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/posts/1")
        assert resp.status_code == 403

    def test_post_inexistente_retorna_404(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/posts/9999")
        assert resp.status_code == 404

    def test_deletar_post_sem_autenticacao_retorna_401(self, client):
        resp = client.delete("/posts/1")
        assert resp.status_code == 401


class TestCompartilharViagemNoFeed:
    def test_admin_compartilha_viagem_publica(self, client_admin):
        conn = _por_bloco([
            [(99,)],                                # get_usuario_logado
            [{"publica": 1}, {"cargo": "admin"}],   # SELECT publica; checar_membro_grupo (cargo)
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.post(
                "/posts",
                data={"conteudo": "Ainda temos vagas!", "tipo": "viagem", "ref_id_grupo": 10},
            )
        assert resp.status_code == 201

    def test_membro_comum_nao_pode_compartilhar_viagem(self, client_usuario):
        conn = _por_bloco([[(1,)], [{"publica": 1}, {"cargo": "membro"}]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"tipo": "viagem", "ref_id_grupo": 10})
        assert resp.status_code == 403

    def test_nao_pode_compartilhar_viagem_privada(self, client_admin):
        conn = _por_bloco([[(99,)], [{"publica": 0}, {"cargo": "admin"}]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.post("/posts", data={"tipo": "viagem", "ref_id_grupo": 10})
        assert resp.status_code == 400
        assert "pública" in resp.json()["detail"]

    def test_viagem_inexistente_retorna_404(self, client_usuario):
        conn = _por_bloco([[(1,)], [None]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"tipo": "viagem", "ref_id_grupo": 999})
        assert resp.status_code == 404

    def test_sem_ref_id_grupo_retorna_400(self, client_usuario):
        conn = _conn_seq([(1,)])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"tipo": "viagem"})
        assert resp.status_code == 400


class TestCompartilharRoteiroNoFeed:
    # O roteiro COMPLETO de uma viagem é o conjunto de itens com aquele
    # id_grupo — não existe um "id de roteiro" separado pra selecionar só um
    # item. Por isso compartilhar roteiro usa ref_id_grupo (mesmo campo de
    # "compartilhar viagem"), e exige que a viagem já tenha ao menos 1 item.
    def test_admin_compartilha_roteiro_mesmo_de_viagem_privada(self, client_admin):
        conn = _por_bloco([
            [(99,)],
            [(1,), {"cargo": "admin"}, {"total": 3}],
        ])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.post("/posts", data={"tipo": "roteiro", "ref_id_grupo": 10})
        assert resp.status_code == 201

    def test_membro_comum_nao_pode_compartilhar_roteiro(self, client_usuario):
        conn = _por_bloco([[(1,)], [(1,), {"cargo": "membro"}]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"tipo": "roteiro", "ref_id_grupo": 10})
        assert resp.status_code == 403

    def test_viagem_inexistente_retorna_404(self, client_usuario):
        conn = _por_bloco([[(1,)], [None]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"tipo": "roteiro", "ref_id_grupo": 999})
        assert resp.status_code == 404

    def test_viagem_sem_itens_no_roteiro_retorna_400(self, client_admin):
        conn = _por_bloco([[(99,)], [(1,), {"cargo": "admin"}, {"total": 0}]])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_admin.post("/posts", data={"tipo": "roteiro", "ref_id_grupo": 10})
        assert resp.status_code == 400

    def test_sem_ref_id_grupo_retorna_400(self, client_usuario):
        conn = _conn_seq([(1,)])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"tipo": "roteiro"})
        assert resp.status_code == 400


class TestFeedComReferencias:
    def test_feed_traz_dados_atuais_da_viagem_referenciada(self, client_usuario):
        posts = [
            {"id_post": 1, "id_grupo": None, "id_comunidade": None, "tipo": "texto",
             "conteudo": "oi", "imagem": None, "data_criacao": "2026-06-01T10:00:00",
             "id_usuario": 1, "nome": "K", "foto_perfil": None, "curtidas": 0, "ja_curtiu": 0,
             "ref_id_grupo": None, "ref_id_roteiro": None},
            {"id_post": 2, "id_grupo": None, "id_comunidade": None, "tipo": "viagem",
             "conteudo": "Vamos!", "imagem": None, "data_criacao": "2026-06-02T10:00:00",
             "id_usuario": 1, "nome": "K", "foto_perfil": None, "curtidas": 0, "ja_curtiu": 0,
             "ref_id_grupo": 10, "ref_id_roteiro": None},
        ]
        grupo_ref = {
            "id_grupo": 10, "nome_grupo": "Japão", "destino_principal": "Tóquio",
            "data_inicio": "2027-07-01", "data_fim": "2027-07-10",
            "limite_participantes": 4, "vagas_ocupadas": 3,
        }

        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                c.fetchall.side_effect = [posts, [], [grupo_ref]]  # base, comentarios, grupos
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/posts")

        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["ref_grupo"] is None
        assert data[1]["ref_grupo"]["nome_grupo"] == "Japão"
        assert data[1]["ref_grupo"]["vagas_ocupadas"] == 3

    def test_feed_traz_todos_os_itens_do_roteiro_compartilhado(self, client_usuario):
        # tipo='roteiro' usa ref_id_grupo (mesmo campo de tipo='viagem') — o
        # roteiro completo e' o CONJUNTO de itens daquele grupo, nunca so 1.
        posts = [
            {"id_post": 3, "id_grupo": None, "id_comunidade": None, "tipo": "roteiro",
             "conteudo": "Nosso roteiro!", "imagem": None, "data_criacao": "2026-06-03T10:00:00",
             "id_usuario": 1, "nome": "K", "foto_perfil": None, "curtidas": 0, "ja_curtiu": 0,
             "ref_id_grupo": 10, "ref_id_roteiro": None},
        ]
        info_grupo = {"id_grupo": 10, "nome_grupo": "Japão", "destino_principal": "Tóquio"}
        itens = [
            {"id_grupo": 10, "titulo": "Dia 1 - Shibuya", "descricao": "manhã"},
            {"id_grupo": 10, "titulo": "Dia 1 - Shinjuku", "descricao": "tarde"},
            {"id_grupo": 10, "titulo": "Dia 2 - Asakusa", "descricao": "manhã"},
        ]

        call_count = [0]

        def factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
            else:
                # base, comentarios, info_grupos (roteiro), itens (roteiro)
                c.fetchall.side_effect = [posts, [], [info_grupo], itens]
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock(); conn.rollback = MagicMock(); conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/posts")

        assert resp.status_code == 200
        ref = resp.json()[0]["ref_roteiro"]
        assert ref["nome_grupo"] == "Japão"
        assert ref["total_itens"] == 3
        assert [i["titulo"] for i in ref["itens"]] == ["Dia 1 - Shibuya", "Dia 1 - Shinjuku", "Dia 2 - Asakusa"]
