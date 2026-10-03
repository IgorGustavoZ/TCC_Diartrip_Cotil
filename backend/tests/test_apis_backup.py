"""test_apis_backup.py — APIs externas secundárias (backup) e a camada de fallback.

Tudo com mock de httpx/OpenAI: nenhum teste sai pra rede. O conftest desliga
os backups globalmente; aqui eles são ligados com patch.dict(os.environ).
"""
import os
import httpx
import openai
import pytest
from unittest.mock import MagicMock, patch

import utils.apis_externas as apis
import utils.osm_client as osm
import utils.openmeteo_client as om
import utils.ia_client as ia

_BACKUP_ON = {"APIS_BACKUP_HABILITADO": "true", "APIS_FORCAR_BACKUP": "false"}
_BACKUP_OFF = {"APIS_BACKUP_HABILITADO": "false", "APIS_FORCAR_BACKUP": "false"}
_SO_BACKUP = {"APIS_BACKUP_HABILITADO": "true", "APIS_FORCAR_BACKUP": "true"}


def _resp(payload):
    r = MagicMock()
    r.json.return_value = payload
    return r


# ── Clientes secundários ─────────────────────────────────────────────────────

class TestOsmClient:
    def test_autocomplete_normaliza_para_formato_geoapify(self):
        payload = {"features": [{
            "geometry": {"coordinates": [2.35, 48.85]},
            "properties": {"name": "Paris", "type": "city", "state": "Île-de-France",
                           "country": "França", "countrycode": "FR"},
        }]}
        with patch("utils.osm_client.httpx.get", return_value=_resp(payload)) as mock_get:
            features = osm.autocomplete("Par")

        p = features[0]["properties"]
        assert p["city"] == "Paris"
        assert p["formatted"] == "Paris, Île-de-France, França"
        assert p["lat"] == 48.85 and p["lon"] == 2.35
        assert p["country_code"] == "fr"
        assert "User-Agent" in mock_get.call_args.kwargs["headers"]

    def test_autocomplete_erro_lanca(self):
        with patch("utils.osm_client.httpx.get", side_effect=Exception("timeout")):
            with pytest.raises(Exception):
                osm.autocomplete("Par")

    def test_geocodificar_sucesso(self):
        with patch("utils.osm_client.httpx.get", return_value=_resp([{"lat": "48.85", "lon": "2.35"}])):
            assert osm.geocodificar("Paris") == (48.85, 2.35)

    def test_geocodificar_sem_resultado_e_erro_retornam_none(self):
        with patch("utils.osm_client.httpx.get", return_value=_resp([])):
            assert osm.geocodificar("Lugar Inexistente") is None
        with patch("utils.osm_client.httpx.get", side_effect=Exception("timeout")):
            assert osm.geocodificar("Paris") is None
        assert osm.geocodificar("") is None

    def test_pois_prioriza_atracoes_e_usa_formato_geoapify(self):
        payload = {"elements": [
            {"type": "node", "lat": 1.0, "lon": 2.0, "tags": {"name": "Bistrô", "amenity": "restaurant"}},
            {"type": "way", "center": {"lat": 3.0, "lon": 4.0},
             "tags": {"name": "Louvre", "tourism": "museum", "addr:street": "Rue de Rivoli",
                      "addr:housenumber": "1", "addr:city": "Paris"}},
            {"type": "node", "lat": 5.0, "lon": 6.0, "tags": {"amenity": "cafe"}},  # sem nome → ignorado
        ]}
        with patch("utils.osm_client.httpx.post", return_value=_resp(payload)):
            pois = osm.buscar_pontos_interesse(48.85, 2.35, limite=5)

        assert pois == [
            {"nome": "Louvre", "categoria": "tourism.museum", "endereco": "Rue de Rivoli 1, Paris",
             "coordenadas": {"lat": 3.0, "lon": 4.0}},
            {"nome": "Bistrô", "categoria": "amenity.restaurant", "endereco": None,
             "coordenadas": {"lat": 1.0, "lon": 2.0}},
        ]

    def test_pois_erro_retorna_vazio(self):
        with patch("utils.osm_client.httpx.post", side_effect=Exception("timeout")):
            assert osm.buscar_pontos_interesse(48.85, 2.35) == []


class TestOpenMeteoClient:
    def test_previsao_mesmo_formato_do_openweather(self):
        payload = {"daily": {
            "time": ["2026-09-10", "2026-09-11"],
            "weather_code": [63, 0],
            "temperature_2m_max": [18, 26],
            "temperature_2m_min": [12, 18],
        }}
        with patch("utils.openmeteo_client.httpx.get", return_value=_resp(payload)):
            previsao = om.previsao_por_dia(48.85, 2.35)

        assert previsao["2026-09-10"] == {"resumo": "chuva moderada, ~15°C", "chuva": True}
        assert previsao["2026-09-11"] == {"resumo": "céu limpo, ~22°C", "chuva": False}

    def test_previsao_erro_retorna_vazio(self):
        with patch("utils.openmeteo_client.httpx.get", side_effect=Exception("timeout")):
            assert om.previsao_por_dia(48.85, 2.35) == {}


# ── Camada de fallback (utils/apis_externas.py) ──────────────────────────────

class TestFallbackGeo:
    def test_principal_ok_nao_chama_backup(self):
        with patch.dict(os.environ, _BACKUP_ON), \
             patch.object(apis.geoapify_client, "geocodificar", return_value=(1.0, 2.0)), \
             patch.object(apis.osm_client, "geocodificar") as backup:
            assert apis.geocodificar("Paris") == (1.0, 2.0)
        backup.assert_not_called()

    def test_principal_sem_resultado_usa_backup(self):
        with patch.dict(os.environ, _BACKUP_ON), \
             patch.object(apis.geoapify_client, "geocodificar", return_value=None), \
             patch.object(apis.osm_client, "geocodificar", return_value=(3.0, 4.0)):
            assert apis.geocodificar("Paris") == (3.0, 4.0)

    def test_backup_desligado_mantem_comportamento_original(self):
        with patch.dict(os.environ, _BACKUP_OFF), \
             patch.object(apis.geoapify_client, "geocodificar", return_value=None), \
             patch.object(apis.osm_client, "geocodificar") as backup:
            assert apis.geocodificar("Paris") is None
        backup.assert_not_called()

    def test_erro_da_requisicao_nao_aciona_backup(self):
        """400 (ex.: moderação) falharia igual no backup: não repassa o prompt."""
        principal = MagicMock()
        principal.chat.completions.create.side_effect = _erro_status(400, "bloqueado")
        secundario = MagicMock()
        with patch.object(ia, "_principal", principal), patch.object(ia, "_backup", (secundario, "llama")),              patch.dict(os.environ, {"IA_MODELOS_BACKUP": "m2", "IA_FORCAR_BACKUP": "false"}):
            with pytest.raises(openai.APIStatusError):
                ia.client.chat.completions.create(model="m1", messages=[])
        assert principal.chat.completions.create.call_count == 1
        secundario.chat.completions.create.assert_not_called()

    def test_forcar_backup_pula_principal(self):
        with patch.dict(os.environ, _SO_BACKUP), \
             patch.object(apis.geoapify_client, "geocodificar") as principal, \
             patch.object(apis.osm_client, "geocodificar", return_value=(3.0, 4.0)):
            assert apis.geocodificar("Paris") == (3.0, 4.0)
        principal.assert_not_called()

    def test_pois_principal_vazio_usa_backup(self):
        poi = {"nome": "Louvre", "categoria": "tourism.museum", "endereco": None, "coordenadas": {"lat": 1, "lon": 2}}
        with patch.dict(os.environ, _BACKUP_ON), \
             patch.object(apis.geoapify_client, "buscar_pontos_interesse", return_value=[]), \
             patch.object(apis.osm_client, "buscar_pontos_interesse", return_value=[poi]) as backup:
            assert apis.buscar_pontos_interesse(1, 2, raio_metros=3000) == [poi]
        assert backup.call_args.kwargs["raio_metros"] == 3000

    def test_autocomplete_principal_falha_usa_backup(self):
        feature = {"properties": {"city": "Paris", "formatted": "Paris, França"}}
        with patch.dict(os.environ, _BACKUP_ON), \
             patch.object(apis.geoapify_client, "autocomplete", side_effect=RuntimeError("sem key")), \
             patch.object(apis.osm_client, "autocomplete", return_value=[feature]):
            assert apis.autocomplete("Par") == [feature]

    def test_autocomplete_ambos_falham_relanca_erro_principal(self):
        with patch.dict(os.environ, _BACKUP_ON), \
             patch.object(apis.geoapify_client, "autocomplete", side_effect=RuntimeError("principal")), \
             patch.object(apis.osm_client, "autocomplete", side_effect=Exception("backup")):
            with pytest.raises(RuntimeError, match="principal"):
                apis.autocomplete("Par")

    def test_autocomplete_backup_desligado_relanca(self):
        with patch.dict(os.environ, _BACKUP_OFF), \
             patch.object(apis.geoapify_client, "autocomplete", side_effect=RuntimeError("sem key")), \
             patch.object(apis.osm_client, "autocomplete") as backup:
            with pytest.raises(RuntimeError):
                apis.autocomplete("Par")
        backup.assert_not_called()

    def test_clima_principal_vazio_usa_open_meteo(self):
        dia = {"2026-09-20": {"resumo": "céu limpo, ~22°C", "chuva": False}}
        with patch.dict(os.environ, _BACKUP_ON), \
             patch.object(apis.openweather_client, "previsao_por_dia", return_value={}), \
             patch.object(apis.openmeteo_client, "previsao_por_dia", return_value=dia):
            assert apis.previsao_por_dia(1, 2) == dia

    def test_rota_autocomplete_usa_backup(self, client_usuario):
        from tests.conftest import make_cursor, make_connection, fake_get_db
        conn = make_connection(make_cursor(rows=[(1,)]))
        feature = {"properties": {"city": "Paris", "formatted": "Paris, França"}}
        with patch.dict(os.environ, _BACKUP_ON), \
             patch("database.get_db", fake_get_db(conn)), \
             patch.object(apis.geoapify_client, "autocomplete", side_effect=RuntimeError("fora do ar")), \
             patch.object(apis.osm_client, "autocomplete", return_value=[feature]):
            resp = client_usuario.get("/geocode/autocomplete?text=Par")
        assert resp.status_code == 200
        assert resp.json()["features"][0]["properties"]["city"] == "Paris"


# ── IA com fallback (utils/ia_client.py) ─────────────────────────────────────

def _erro_status(status: int, msg: str = "erro") -> openai.APIStatusError:
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    return openai.APIStatusError(f"Error code: {status} {msg}", response=httpx.Response(status, request=req), body=None)


def _erro_conexao() -> openai.APIConnectionError:
    return openai.APIConnectionError(request=httpx.Request("POST", "http://localhost:11434/v1"))


class TestFallbackIA:
    def _fake(self, texto="ok"):
        r = MagicMock()
        r.choices = [MagicMock(message=MagicMock(content=texto))]
        return r

    def test_sem_backup_configurado_comportamento_original(self):
        principal = MagicMock()
        principal.chat.completions.create.side_effect = Exception("Error code: 402")
        with patch.object(ia, "_principal", principal), patch.object(ia, "_backup", None), \
             patch.dict(os.environ, {"IA_MODELOS_BACKUP": "", "IA_FORCAR_BACKUP": "false"}):
            with pytest.raises(Exception, match="402"):
                ia.client.chat.completions.create(model="m1", messages=[])
        assert principal.chat.completions.create.call_count == 1

    def test_principal_ok(self):
        principal = MagicMock()
        principal.chat.completions.create.return_value = self._fake("oi")
        with patch.object(ia, "_principal", principal), patch.object(ia, "_backup", None):
            r = ia.client.chat.completions.create(model="m1", messages=[], max_tokens=10)
        assert r.choices[0].message.content == "oi"
        principal.chat.completions.create.assert_called_once_with(model="m1", messages=[], max_tokens=10)

    def test_tenta_modelos_backup_do_openrouter(self):
        principal = MagicMock()
        principal.chat.completions.create.side_effect = [_erro_status(404, "modelo fora"), self._fake("backup")]
        with patch.object(ia, "_principal", principal), patch.object(ia, "_backup", None), \
             patch.dict(os.environ, {"IA_MODELOS_BACKUP": "m1, m2", "IA_FORCAR_BACKUP": "false"}):
            r = ia.client.chat.completions.create(model="m1", messages=[])
        assert r.choices[0].message.content == "backup"
        modelos = [c.kwargs["model"] for c in principal.chat.completions.create.call_args_list]
        assert modelos == ["m1", "m2"]  # m1 não é repetido

    def test_provedor_secundario_e_erro_principal_preservado(self):
        principal = MagicMock()
        principal.chat.completions.create.side_effect = _erro_status(402, "credits")
        secundario = MagicMock()
        secundario.chat.completions.create.side_effect = _erro_conexao()
        with patch.object(ia, "_principal", principal), patch.object(ia, "_backup", (secundario, "llama")), \
             patch.dict(os.environ, {"IA_MODELOS_BACKUP": "", "IA_FORCAR_BACKUP": "false"}):
            with pytest.raises(Exception, match="402"):
                ia.client.chat.completions.create(model="m1", messages=[])
        assert secundario.chat.completions.create.call_args.kwargs["model"] == "llama"

    def test_erro_da_requisicao_nao_aciona_backup(self):
        """400 (ex.: moderação) falharia igual no backup: não repassa o prompt."""
        principal = MagicMock()
        principal.chat.completions.create.side_effect = _erro_status(400, "bloqueado")
        secundario = MagicMock()
        with patch.object(ia, "_principal", principal), patch.object(ia, "_backup", (secundario, "llama")),              patch.dict(os.environ, {"IA_MODELOS_BACKUP": "m2", "IA_FORCAR_BACKUP": "false"}):
            with pytest.raises(openai.APIStatusError):
                ia.client.chat.completions.create(model="m1", messages=[])
        assert principal.chat.completions.create.call_count == 1
        secundario.chat.completions.create.assert_not_called()

    def test_forcar_backup_pula_principal(self):
        principal = MagicMock()
        secundario = MagicMock()
        secundario.chat.completions.create.return_value = self._fake("groq")
        with patch.object(ia, "_principal", principal), patch.object(ia, "_backup", (secundario, "llama")), \
             patch.dict(os.environ, {"IA_MODELOS_BACKUP": "", "IA_FORCAR_BACKUP": "true"}):
            r = ia.client.chat.completions.create(model="m1", messages=[])
        assert r.choices[0].message.content == "groq"
        principal.chat.completions.create.assert_not_called()


class TestLogSeguro:
    def test_erro_http_nao_expoe_api_key(self):
        from utils.log_seguro import descrever_erro

        req = httpx.Request("GET", "https://api.geoapify.com/v1/geocode/search?apiKey=SEGREDO123")
        with pytest.raises(httpx.HTTPStatusError) as info:
            httpx.Response(401, request=req).raise_for_status()
        exc = info.value
        assert "SEGREDO123" in str(exc)  # o motivo do helper existir
        assert "SEGREDO123" not in descrever_erro(exc)
        assert descrever_erro(exc) == "HTTP 401"
