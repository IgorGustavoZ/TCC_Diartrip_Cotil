"""
test_posts.py — Testes de posts com banco mockado.
"""
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


# =========================================================================== #
# Criar post
# =========================================================================== #

class TestCriarPost:
    def test_criar_post_texto_simples(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "Minha primeira viagem!"})
        assert resp.status_code == 200
        data = resp.json()
        assert "id_post" in data or "mensagem" in data

    def test_criar_post_com_imagem_valida(self, client_usuario):
        conn = _conn_seq([(1,), None])
        fake_url = "https://res.cloudinary.com/test/image/upload/v1/abc.jpg"

        with patch("database.get_db", fake_get_db(conn)), \
             patch("utils.cloudinary_upload.upload_imagem", return_value=fake_url), \
             patch("utils.imagem_utils.strip_exif", side_effect=lambda b, e: b):
            resp = client_usuario.post(
                "/posts",
                data={"conteudo": "Com foto!"},
                files={"imagem": ("foto.jpg", JPEG_MAGIC, "image/jpeg")},
            )

        assert resp.status_code == 200

    def test_criar_post_conteudo_vazio_retorna_400(self, client_usuario):
        conn = _conn_seq([(1,)])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "   "})
        assert resp.status_code == 400

    def test_criar_post_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/posts", data={"conteudo": "teste"})
        assert resp.status_code == 401

    def test_criar_post_conteudo_muito_longo_retorna_422(self, client_usuario):
        conn = _conn_seq([(1,)])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/posts", data={"conteudo": "A" * 5001})
        assert resp.status_code == 422


# =========================================================================== #
# Listar posts
# =========================================================================== #

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


# =========================================================================== #
# Deletar post
# =========================================================================== #

class TestDeletarPost:
    def test_dono_pode_deletar_proprio_post(self, client_usuario):
        # SELECT retorna (id_usuario=1, imagem=None) — token e id=1
        conn = _conn_seq([(1,), (1, None), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/posts/1")
        assert resp.status_code == 200

    def test_outro_usuario_nao_pode_deletar_post(self, client_usuario):
        # post pertence ao usuario 2, token id=1
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
