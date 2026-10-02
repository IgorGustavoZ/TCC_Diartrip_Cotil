"""test_comunidades.py — Comunidades (grupos temáticos, não são viagens)."""
from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db, make_connection, make_cursor, JPEG_MAGIC

COMUNIDADE_PAYLOAD = {
    "nome": "Amantes do Japão",
    "descricao": "Para quem ama viajar para o Japão",
    "categoria": "Japão",
    "privacidade": "publica",
}


class TestCriarComunidade:
    def test_usuario_pode_criar_comunidade(self, client_usuario):
        cur = make_cursor(rows=[(1,)], lastrowid=7)
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/comunidades", json=COMUNIDADE_PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["id_comunidade"] == 7

    def test_criador_vira_admin_da_comunidade(self, client_usuario):
        cur = make_cursor(rows=[(1,)], lastrowid=7)
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/comunidades", json=COMUNIDADE_PAYLOAD)
        assert resp.status_code == 201
        insert_membro = next(
            c for c in cur.execute.call_args_list if "INSERT INTO comunidade_membros" in c.args[0]
        )
        assert "'admin'" in insert_membro.args[0]
        assert insert_membro.args[1] == (7, 1)

    def test_nome_muito_curto_retorna_422(self, client_usuario):
        payload = dict(COMUNIDADE_PAYLOAD, nome="Ja")
        resp = client_usuario.post("/comunidades", json=payload)
        assert resp.status_code == 422

    def test_privacidade_invalida_retorna_422(self, client_usuario):
        payload = dict(COMUNIDADE_PAYLOAD, privacidade="secreta")
        resp = client_usuario.post("/comunidades", json=payload)
        assert resp.status_code == 422

    def test_criar_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/comunidades", json=COMUNIDADE_PAYLOAD)
        assert resp.status_code == 401


class TestListarComunidades:
    def test_lista_comunidades(self, client_usuario):
        comunidade = {
            "id_comunidade": 1, "nome": "Amantes do Japão", "descricao": "desc",
            "categoria": "Japão", "privacidade": "publica", "criado_por": 5,
            "criador": "Maria", "total_membros": 3, "sou_membro": 0,
        }
        cur = MagicMock()
        cur.fetchone.return_value = (1,)
        cur.fetchall.return_value = [comunidade]
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["sou_membro"] is False

    def test_listar_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/comunidades")
        assert resp.status_code == 401


class TestDetalharComunidade:
    def test_comunidade_publica_qualquer_um_ve(self, client_usuario):
        cur = make_cursor(rows=[
            (1,),
            {"id_comunidade": 1, "nome": "Amantes do Japão", "descricao": None,
             "categoria": "Japão", "privacidade": "publica", "criado_por": 5,
             "criador": "Maria", "total_membros": 3},
            None,  # nao e' membro
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sou_membro"] is False
        assert data["meu_cargo"] is None

    def test_comunidade_privada_nao_membro_recebe_403(self, client_usuario):
        cur = make_cursor(rows=[
            (1,),
            {"id_comunidade": 1, "nome": "Clube fechado", "descricao": None,
             "categoria": None, "privacidade": "privada", "criado_por": 5,
             "criador": "Maria", "total_membros": 3},
            None,
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/1")
        assert resp.status_code == 403

    def test_comunidade_privada_membro_ve_normalmente(self, client_usuario):
        cur = make_cursor(rows=[
            (1,),
            {"id_comunidade": 1, "nome": "Clube fechado", "descricao": None,
             "categoria": None, "privacidade": "privada", "criado_por": 5,
             "criador": "Maria", "total_membros": 3},
            {"cargo": "membro"},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/1")
        assert resp.status_code == 200
        assert resp.json()["sou_membro"] is True

    def test_comunidade_inexistente_retorna_404(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/999")
        assert resp.status_code == 404


class TestEntrarComunidade:
    def test_entra_em_comunidade_publica(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"privacidade": "publica"}, None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/comunidades/1/entrar")
        assert resp.status_code == 200

    def test_nao_pode_entrar_em_comunidade_privada_sozinho(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"privacidade": "privada"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/comunidades/1/entrar")
        assert resp.status_code == 403

    def test_ja_e_membro_retorna_400(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"privacidade": "publica"}, (1,)])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/comunidades/1/entrar")
        assert resp.status_code == 400

    def test_comunidade_inexistente_retorna_404(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/comunidades/999/entrar")
        assert resp.status_code == 404

    def test_entrar_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/comunidades/1/entrar")
        assert resp.status_code == 401


class TestSairComunidade:
    def test_membro_sai_da_comunidade(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"criado_por": 5}], rowcount=1)
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/comunidades/1/sair")
        assert resp.status_code == 200

    def test_criador_nao_pode_sair(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"criado_por": 1}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/comunidades/1/sair")
        assert resp.status_code == 400

    def test_nao_membro_recebe_400(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"criado_por": 5}], rowcount=0)
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/comunidades/1/sair")
        assert resp.status_code == 400

    def test_comunidade_inexistente_retorna_404(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/comunidades/999/sair")
        assert resp.status_code == 404


class TestPostsDaComunidade:
    def test_membro_pode_listar_posts(self, client_usuario):
        cur = MagicMock()
        cur.fetchone.side_effect = [(1,), {"cargo": "membro"}]
        cur.fetchall.return_value = []
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/1/posts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_nao_membro_nao_pode_listar_posts(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/1/posts")
        assert resp.status_code == 403

    def test_membro_pode_publicar_na_comunidade(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "Alguém já foi a Osaka?", "id_comunidade": 1})
        assert resp.status_code == 201

    def test_nao_membro_nao_pode_publicar_na_comunidade(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "Intruso", "id_comunidade": 1})
        assert resp.status_code == 403


class TestAtualizarComunidade:
    def test_admin_pode_atualizar(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "admin"}], rowcount=1)
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/comunidades/1", json=COMUNIDADE_PAYLOAD)
        assert resp.status_code == 200

    def test_membro_comum_nao_pode_atualizar(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/comunidades/1", json=COMUNIDADE_PAYLOAD)
        assert resp.status_code == 403

    def test_nao_membro_nao_pode_atualizar(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.put("/comunidades/1", json=COMUNIDADE_PAYLOAD)
        assert resp.status_code == 403


def _conn_excluir(fetchones, imagens_posts=None):
    # excluir() usa fetchone pra autenticação/cargo/foto_capa e um fetchall
    # separado pra imagens dos posts — o helper genérico make_cursor() faz
    # fetchall devolver TODAS as rows passadas (não só as de posts), então
    # aqui cada um tem sua própria sequência/retorno independente.
    fetch_idx = [0]

    def factory(**kw):
        c = MagicMock()
        c.rowcount = 1

        def _fetchone():
            i = fetch_idx[0]
            fetch_idx[0] += 1
            return fetchones[i] if i < len(fetchones) else None

        c.fetchone.side_effect = _fetchone
        c.fetchall.return_value = imagens_posts or []
        return c

    conn = MagicMock()
    conn.cursor.side_effect = factory
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


class TestExcluirComunidade:
    def test_admin_pode_excluir(self, client_usuario):
        conn = _conn_excluir([(1,), {"cargo": "admin"}, {"foto_capa": None}])
        with patch("services.comunidade_service.deletar_imagem") as mock_del, \
             patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/comunidades/1")
        assert resp.status_code == 200
        mock_del.assert_not_called()  # sem foto_capa e sem posts com imagem

    def test_excluir_apaga_imagens_no_cloudinary(self, client_usuario):
        conn = _conn_excluir(
            [(1,), {"cargo": "admin"}, {"foto_capa": "https://cloud/capa.jpg"}],
            imagens_posts=[{"imagem": "https://cloud/post1.jpg"}],
        )
        with patch("services.comunidade_service.deletar_imagem") as mock_del, \
             patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/comunidades/1")
        assert resp.status_code == 200
        urls = [c.args[0] for c in mock_del.call_args_list]
        assert "https://cloud/capa.jpg" in urls
        assert "https://cloud/post1.jpg" in urls

    def test_membro_comum_nao_pode_excluir(self, client_usuario):
        conn = _conn_excluir([(1,), {"cargo": "membro"}])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/comunidades/1")
        assert resp.status_code == 403

    def test_nao_membro_nao_pode_excluir(self, client_usuario):
        conn = _conn_excluir([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/comunidades/1")
        assert resp.status_code == 403

    def test_excluir_sem_autenticacao_retorna_401(self, client):
        resp = client.delete("/comunidades/1")
        assert resp.status_code == 401


class TestCodigoConviteComunidade:
    def test_admin_ve_codigo_de_comunidade_privada(self, client_usuario):
        cur = make_cursor(rows=[
            (1,), {"cargo": "admin"}, {"codigo_convite": "JAPAO2", "privacidade": "privada"},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/1/codigo-convite")
        assert resp.status_code == 200
        assert resp.json()["codigo_convite"] == "JAPAO2"

    def test_admin_nao_ve_codigo_de_comunidade_publica(self, client_usuario):
        # Código de convite só existe pra quando a comunidade é privada —
        # pública não precisa (nem deve) expor um código.
        cur = make_cursor(rows=[
            (1,), {"cargo": "admin"}, {"codigo_convite": "JAPAO2", "privacidade": "publica"},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/1/codigo-convite")
        assert resp.status_code == 400

    def test_membro_comum_nao_ve_codigo(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/1/codigo-convite")
        assert resp.status_code == 403

    def test_nao_membro_nao_ve_codigo(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/comunidades/1/codigo-convite")
        assert resp.status_code == 403


class TestFotoComunidade:
    def test_admin_pode_trocar_foto(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "admin"}])
        conn = make_connection(cur)
        fake_url = "https://res.cloudinary.com/test/image/upload/v1/comunidade_1.jpg"
        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.comunidade_service.upload_imagem", return_value=fake_url), \
             patch("services.comunidade_service.strip_exif", side_effect=lambda b, e: b), \
             patch("utils.imagem_utils._validar_dimensoes"):
            resp = client_usuario.patch(
                "/comunidades/1/foto",
                files={"foto": ("capa.jpg", JPEG_MAGIC, "image/jpeg")},
            )
        assert resp.status_code == 200
        assert resp.json()["foto_capa"] == fake_url

    def test_membro_comum_nao_pode_trocar_foto(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.patch(
                "/comunidades/1/foto",
                files={"foto": ("capa.jpg", JPEG_MAGIC, "image/jpeg")},
            )
        assert resp.status_code == 403


class TestEntrarComunidadePrivadaComCodigo:
    def test_entra_com_codigo_correto(self, client_usuario):
        cur = make_cursor(rows=[
            (1,), {"privacidade": "privada", "codigo_convite": "JAPAO2"}, None,
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/comunidades/1/entrar", json={"codigo": "japao2"})
        assert resp.status_code == 200

    def test_nao_entra_com_codigo_errado(self, client_usuario):
        cur = make_cursor(rows=[
            (1,), {"privacidade": "privada", "codigo_convite": "JAPAO2"},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/comunidades/1/entrar", json={"codigo": "ERRADO"})
        assert resp.status_code == 403

    def test_nao_entra_sem_informar_codigo(self, client_usuario):
        cur = make_cursor(rows=[
            (1,), {"privacidade": "privada", "codigo_convite": "JAPAO2"},
        ])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/comunidades/1/entrar")
        assert resp.status_code == 403
