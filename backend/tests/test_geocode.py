"""test_geocode.py — Proxy de autocomplete de cidade (Geoapify), key só no backend."""
from unittest.mock import MagicMock, patch

from tests.conftest import make_cursor, make_connection, fake_get_db


class TestGeocodeAutocomplete:
    def test_autocomplete_com_sucesso(self, client_usuario):
        cur = make_cursor(rows=[(1,)])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("routes.geocode.autocomplete", return_value=[
                 {"properties": {"city": "Paris", "formatted": "Paris, França"}}
             ]):
            resp = client_usuario.get("/geocode/autocomplete?text=Par")

        assert resp.status_code == 200
        data = resp.json()
        assert data["features"][0]["properties"]["city"] == "Paris"

    def test_autocomplete_indisponivel_retorna_502(self, client_usuario):
        cur = make_cursor(rows=[(1,)])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("routes.geocode.autocomplete", side_effect=Exception("timeout")):
            resp = client_usuario.get("/geocode/autocomplete?text=Par")

        assert resp.status_code == 502

    def test_autocomplete_sem_texto_retorna_422(self, client_usuario):
        resp = client_usuario.get("/geocode/autocomplete?text=")
        assert resp.status_code == 422

    def test_autocomplete_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/geocode/autocomplete?text=Par")
        assert resp.status_code == 401

    def test_nao_expoe_api_key_na_resposta(self, client_usuario):
        cur = make_cursor(rows=[(1,)])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("routes.geocode.autocomplete", return_value=[]):
            resp = client_usuario.get("/geocode/autocomplete?text=Par")

        assert "apiKey" not in resp.text
        assert "803e071045c64d13a3dbb8c9058c323a" not in resp.text
