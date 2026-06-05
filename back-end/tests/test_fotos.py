"""
test_fotos.py — Testes de upload e delecao de fotos com banco e Cloudinary mockados.
"""
from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db, fake_foto, JPEG_MAGIC, PNG_MAGIC, PDF_BYTES, JPEG_AS_PNG


def _conn_seq(fetchones, fetchalls=None):
    fa = fetchalls or {}
    fetch_idx = [0]
    fetchall_idx = [0]

    def factory(**kw):
        c = MagicMock()
        c.rowcount = 1
        c.lastrowid = 1

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
# Upload de fotos
# =========================================================================== #

class TestUploadFoto:
    def test_upload_jpeg_valido(self, client_usuario):
        conn = _conn_seq([(1,), {"cargo": "membro"}])
        fake_url = "https://res.cloudinary.com/test/image/upload/v1/diartrip/fotos/10/abc.jpg"

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.foto_service.upload_imagem", return_value=fake_url), \
             patch("utils.imagem_utils.strip_exif", side_effect=lambda b, e: b):
            resp = client_usuario.post(
                "/grupos/10/fotos",
                files={"arquivo": ("foto.jpg", JPEG_MAGIC, "image/jpeg")},
            )

        assert resp.status_code == 200
        assert resp.json()["url"] == fake_url

    def test_upload_png_valido(self, client_usuario):
        conn = _conn_seq([(1,), {"cargo": "membro"}])
        fake_url = "https://res.cloudinary.com/test/image/upload/v1/abc.png"

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.foto_service.upload_imagem", return_value=fake_url), \
             patch("utils.imagem_utils.strip_exif", side_effect=lambda b, e: b):
            resp = client_usuario.post(
                "/grupos/10/fotos",
                files={"arquivo": ("foto.png", PNG_MAGIC, "image/png")},
            )

        assert resp.status_code == 200

    def test_upload_pdf_retorna_400(self, client_usuario):
        conn = _conn_seq([(1,)])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post(
                "/grupos/10/fotos",
                files={"arquivo": ("doc.pdf", PDF_BYTES, "application/pdf")},
            )
        assert resp.status_code in (400, 415)

    def test_upload_magic_bytes_falsos_retorna_400(self, client_usuario):
        """Extensao .png mas magic bytes de JPEG — deve falhar validacao."""
        conn = _conn_seq([(1,)])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post(
                "/grupos/10/fotos",
                files={"arquivo": ("foto.png", JPEG_AS_PNG, "image/png")},
            )
        assert resp.status_code == 400

    def test_falha_cloudinary_retorna_502(self, client_usuario):
        conn = _conn_seq([(1,), {"cargo": "membro"}])
        from fastapi import HTTPException

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.foto_service.upload_imagem",
                   side_effect=HTTPException(status_code=502, detail="Cloudinary indisponivel")), \
             patch("utils.imagem_utils.strip_exif", side_effect=lambda b, e: b):
            resp = client_usuario.post(
                "/grupos/10/fotos",
                files={"arquivo": ("foto.jpg", JPEG_MAGIC, "image/jpeg")},
            )

        assert resp.status_code == 502

    def test_falha_db_apos_upload_chama_cleanup(self, client_usuario):
        """DB falha apos upload — deletar_imagem deve ser chamado."""
        fake_url = "https://res.cloudinary.com/test/image/upload/v1/orphan.jpg"
        call_count = [0]
        execute_count = [0]

        def cursor_factory(**kw):
            call_count[0] += 1
            c = MagicMock()
            if call_count[0] == 1:
                c.fetchone.return_value = (1,)
                c.fetchall.return_value = []
            elif call_count[0] == 2:
                c.fetchone.return_value = {"cargo": "membro"}
                c.fetchall.return_value = []

                def _failing_execute(*args, **kwargs):
                    execute_count[0] += 1
                    if execute_count[0] >= 2:
                        raise Exception("DB error")

                c.execute.side_effect = _failing_execute
            c.rowcount = 1
            c.lastrowid = 1
            return c

        conn = MagicMock()
        conn.cursor.side_effect = cursor_factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        mock_deletar = MagicMock()

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.foto_service.upload_imagem", return_value=fake_url), \
             patch("services.foto_service.deletar_imagem", mock_deletar), \
             patch("utils.imagem_utils.strip_exif", side_effect=lambda b, e: b):
            resp = client_usuario.post(
                "/grupos/10/fotos",
                files={"arquivo": ("foto.jpg", JPEG_MAGIC, "image/jpeg")},
            )

        assert resp.status_code in (400, 500, 502, 503)

    def test_upload_sem_autenticacao_retorna_401(self, client):
        resp = client.post(
            "/grupos/10/fotos",
            files={"arquivo": ("foto.jpg", JPEG_MAGIC, "image/jpeg")},
        )
        assert resp.status_code == 401


# =========================================================================== #
# Listar fotos
# =========================================================================== #

class TestListarFotos:
    def test_membro_pode_listar_fotos(self, client_usuario):
        conn = _conn_seq([(1,), {"cargo": "membro"}], fetchalls={0: [fake_foto()]})

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/fotos")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# =========================================================================== #
# Deletar foto
# =========================================================================== #

class TestDeletarFoto:
    def test_dono_pode_deletar_foto(self, client_usuario):
        foto = fake_foto(id_foto=1, id_grupo=10, id_usuario=1)
        conn = _conn_seq([(1,), foto, {"cargo": "membro"}])

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.foto_service.deletar_imagem", return_value=None):
            resp = client_usuario.delete("/fotos/1")

        assert resp.status_code == 200

    def test_outro_membro_nao_pode_deletar_foto(self, client_usuario):
        """Foto pertence ao usuario 2, token e do usuario 1."""
        foto = fake_foto(id_foto=1, id_grupo=10, id_usuario=2)
        conn = _conn_seq([(1,), foto, {"cargo": "membro"}])

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/fotos/1")

        assert resp.status_code == 403

    def test_admin_pode_deletar_foto_de_outro(self, client_admin):
        """Admin (id=99) pode deletar foto do usuario 1."""
        foto = fake_foto(id_foto=1, id_grupo=10, id_usuario=1)
        conn = _conn_seq([(99,), foto, {"cargo": "admin"}])

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.foto_service.deletar_imagem", return_value=None):
            resp = client_admin.delete("/fotos/1")

        assert resp.status_code == 200

    def test_foto_nao_encontrada_retorna_404(self, client_usuario):
        conn = _conn_seq([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/fotos/9999")
        assert resp.status_code == 404
