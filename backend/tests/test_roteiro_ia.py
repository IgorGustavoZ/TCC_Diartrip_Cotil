"""test_roteiro_ia.py — Geração de roteiro por IA (mesma tabela roteiros)."""
import json
import pytest
from unittest.mock import MagicMock, patch

from tests.conftest import make_cursor, make_connection, fake_get_db


@pytest.fixture(autouse=True)
def _bypass_rate_limit_local():
    # services/roteiro_ia_service.py importa verificar_rate_limit via
    # "from utils.rate_limiter import ...", então o bypass autouse global
    # (que faz patch em utils.rate_limiter.verificar_rate_limit) não alcança
    # esse nome já vinculado localmente no módulo — precisa ser patchado aqui.
    with patch("services.roteiro_ia_service.verificar_rate_limit", return_value=None):
        yield


def _fake_grupo(destino="Paris", data_inicio="2026-09-10", data_fim="2026-09-12", preferencias=None):
    return {
        "nome_grupo": "Viagem Teste",
        "destino_principal": destino,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "orcamento": 4000.0,
        "tipo_viagem": "cultural",
        "preferencias": preferencias,
    }


def _fake_ia(conteudo: str):
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(content=conteudo))]
    return resp


_JSON_VALIDO = json.dumps({
    "itens": [
        {"titulo": "Dia 1 · 09:00 — Café da manhã", "descricao": "Perto do hotel. Preço não informado."},
        {"titulo": "Dia 1 · 10:00 — Museu do Louvre", "descricao": "Visita guiada."},
    ]
})


class TestGerarRoteiroIA:
    def test_gerar_com_sucesso(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo()])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=(48.85, 2.35)), \
             patch("services.roteiro_ia_service.buscar_pontos_interesse", return_value=[
                 {"nome": "Museu do Louvre", "categoria": "tourism.sights", "endereco": "Paris", "coordenadas": {"lat": 1, "lon": 1}}
             ]), \
             patch("services.roteiro_ia_service.previsao_por_dia", return_value={}), \
             patch("services.roteiro_ia_service._client") as mock_client, \
             patch("services.roteiro_ia_service.roteiro_service.criar", return_value={"mensagem": "ok", "id": 1}) as mock_criar, \
             patch("services.roteiro_ia_service.roteiro_service.listar_por_grupo", return_value=[]) as mock_listar:
            mock_client.chat.completions.create.return_value = _fake_ia(_JSON_VALIDO)
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 200
        assert mock_criar.call_count == 2
        for call in mock_criar.call_args_list:
            assert call.kwargs.get("origem_ia") is True or call.args[-1] is True
        mock_listar.assert_called_once()

    def test_previsao_disponivel_entra_no_prompt(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo(data_inicio="2026-09-10", data_fim="2026-09-11")])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=(48.85, 2.35)), \
             patch("services.roteiro_ia_service.buscar_pontos_interesse", return_value=[]), \
             patch("services.roteiro_ia_service.previsao_por_dia", return_value={
                 "2026-09-10": {"resumo": "Chuva leve, ~15°C", "chuva": True},
             }), \
             patch("services.roteiro_ia_service._client") as mock_client, \
             patch("services.roteiro_ia_service.roteiro_service.criar", return_value={"mensagem": "ok", "id": 1}), \
             patch("services.roteiro_ia_service.roteiro_service.listar_por_grupo", return_value=[]):
            mock_client.chat.completions.create.return_value = _fake_ia(_JSON_VALIDO)
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 200
        prompt_enviado = mock_client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
        assert "PREVISAO_TEMPO" in prompt_enviado
        assert "Chuva leve" in prompt_enviado

    def test_previsao_indisponivel_ainda_gera_roteiro(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo()])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=(48.85, 2.35)), \
             patch("services.roteiro_ia_service.buscar_pontos_interesse", return_value=[]), \
             patch("services.roteiro_ia_service.previsao_por_dia", return_value={}), \
             patch("services.roteiro_ia_service._client") as mock_client, \
             patch("services.roteiro_ia_service.roteiro_service.criar", return_value={"mensagem": "ok", "id": 1}), \
             patch("services.roteiro_ia_service.roteiro_service.listar_por_grupo", return_value=[]):
            mock_client.chat.completions.create.return_value = _fake_ia(_JSON_VALIDO)
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 200
        prompt_enviado = mock_client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
        assert "PREVISAO_TEMPO" not in prompt_enviado

    def test_sem_destino_retorna_400(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo(destino=None)])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 400

    def test_sem_datas_retorna_400(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo(data_inicio=None, data_fim=None)])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 400

    def test_nao_membro_recebe_403(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 403

    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/grupos/10/roteiros/gerar-ia")
        assert resp.status_code == 401

    def test_geoapify_indisponivel_ainda_gera_roteiro(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo()])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=None), \
             patch("services.roteiro_ia_service.buscar_pontos_interesse", return_value=[]) as mock_pois, \
             patch("services.roteiro_ia_service._client") as mock_client, \
             patch("services.roteiro_ia_service.roteiro_service.criar", return_value={"mensagem": "ok", "id": 1}), \
             patch("services.roteiro_ia_service.roteiro_service.listar_por_grupo", return_value=[]):
            mock_client.chat.completions.create.return_value = _fake_ia(_JSON_VALIDO)
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 200
        mock_pois.assert_not_called()  # sem coordenadas, nem tenta buscar POIs

    def test_ia_retorna_json_invalido_retorna_502(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo()])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=None), \
             patch("services.roteiro_ia_service._client") as mock_client:
            mock_client.chat.completions.create.return_value = _fake_ia("isso não é um JSON")
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 502
        assert "técnic" not in resp.json()["detail"].lower()

    def test_ia_sem_itens_retorna_502(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo()])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=None), \
             patch("services.roteiro_ia_service._client") as mock_client:
            mock_client.chat.completions.create.return_value = _fake_ia(json.dumps({"itens": []}))
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 502

    def test_ia_indisponivel_retorna_502(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo()])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=None), \
             patch("services.roteiro_ia_service._client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("timeout")
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 502

    def test_ia_sem_creditos_retorna_mensagem_especifica_sem_retentar(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo()])
        conn = make_connection(cur)

        erro_402 = Exception(
            "Error code: 402 - {'error': {'message': 'This request requires more credits, "
            "or fewer max_tokens.', 'code': 402}}"
        )

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=None), \
             patch("services.roteiro_ia_service._client") as mock_client:
            mock_client.chat.completions.create.side_effect = erro_402
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 502
        assert "crédito" in resp.json()["detail"].lower()
        # erro de créditos nunca é resolvido por retry — só 1 chamada, não 2
        assert mock_client.chat.completions.create.call_count == 1

    def test_data_fim_antes_do_inicio_retorna_400(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo(data_inicio="2026-09-12", data_fim="2026-09-10")])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 400

    def test_preferencias_entram_no_prompt(self, client_usuario):
        cur = make_cursor(rows=[
            (1,), {"cargo": "membro"},
            _fake_grupo(preferencias="Participantes: 4 | Transporte: carro | gastronomia, vida noturna"),
        ])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=(48.85, 2.35)), \
             patch("services.roteiro_ia_service.buscar_pontos_interesse", return_value=[]) as mock_pois, \
             patch("services.roteiro_ia_service.previsao_por_dia", return_value={}), \
             patch("services.roteiro_ia_service._client") as mock_client, \
             patch("services.roteiro_ia_service.roteiro_service.criar", return_value={"mensagem": "ok", "id": 1}), \
             patch("services.roteiro_ia_service.roteiro_service.listar_por_grupo", return_value=[]):
            mock_client.chat.completions.create.return_value = _fake_ia(_JSON_VALIDO)
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 200
        prompt_enviado = mock_client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
        assert "Participantes: 4" in prompt_enviado
        assert "carro" in prompt_enviado
        assert "gastronomia, vida noturna" in prompt_enviado
        # transporte "carro" amplia o raio de busca de pontos de interesse
        assert mock_pois.call_args.kwargs.get("raio_metros") == 10000

    def test_transporte_a_pe_reduz_raio_de_busca(self, client_usuario):
        cur = make_cursor(rows=[
            (1,), {"cargo": "membro"},
            _fake_grupo(preferencias="Transporte: a pé"),
        ])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=(48.85, 2.35)), \
             patch("services.roteiro_ia_service.buscar_pontos_interesse", return_value=[]) as mock_pois, \
             patch("services.roteiro_ia_service.previsao_por_dia", return_value={}), \
             patch("services.roteiro_ia_service._client") as mock_client, \
             patch("services.roteiro_ia_service.roteiro_service.criar", return_value={"mensagem": "ok", "id": 1}), \
             patch("services.roteiro_ia_service.roteiro_service.listar_por_grupo", return_value=[]):
            mock_client.chat.completions.create.return_value = _fake_ia(_JSON_VALIDO)
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 200
        assert mock_pois.call_args.kwargs.get("raio_metros") == 1500

    def test_sem_preferencias_prompt_indica_nao_informado(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}, _fake_grupo()])
        conn = make_connection(cur)

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.roteiro_ia_service.geocodificar", return_value=None), \
             patch("services.roteiro_ia_service._client") as mock_client, \
             patch("services.roteiro_ia_service.roteiro_service.criar", return_value={"mensagem": "ok", "id": 1}), \
             patch("services.roteiro_ia_service.roteiro_service.listar_por_grupo", return_value=[]):
            mock_client.chat.completions.create.return_value = _fake_ia(_JSON_VALIDO)
            resp = client_usuario.post("/grupos/10/roteiros/gerar-ia")

        assert resp.status_code == 200
        prompt_enviado = mock_client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
        assert "Participantes: não informado" in prompt_enviado
        assert "Meio de transporte: não informado" in prompt_enviado


class TestExtrairPreferencias:
    def test_extrai_participantes_e_transporte(self):
        from services.roteiro_ia_service import _extrair_preferencias
        r = _extrair_preferencias("Participantes: 3 | Transporte: carro | gastronomia")
        assert r == {"participantes": 3, "transporte": "carro", "interesses": "gastronomia"}

    def test_apenas_texto_livre_vira_interesses(self):
        from services.roteiro_ia_service import _extrair_preferencias
        r = _extrair_preferencias("praias e mergulho")
        assert r["participantes"] is None
        assert r["transporte"] is None
        assert r["interesses"] == "praias e mergulho"

    def test_vazio_ou_none_retorna_tudo_none(self):
        from services.roteiro_ia_service import _extrair_preferencias
        assert _extrair_preferencias(None) == {"participantes": None, "transporte": None, "interesses": None}
        assert _extrair_preferencias("") == {"participantes": None, "transporte": None, "interesses": None}

    def test_multiplos_interesses_livres_sao_unidos(self):
        from services.roteiro_ia_service import _extrair_preferencias
        r = _extrair_preferencias("Transporte: metrô | não gosto de museus | não quero lugares caros")
        assert r["transporte"] == "metrô"
        assert r["interesses"] == "não gosto de museus, não quero lugares caros"


class TestRaioPorTransporte:
    def test_a_pe_reduz_raio(self):
        from services.roteiro_ia_service import _raio_por_transporte
        assert _raio_por_transporte("a pé") == 1500
        assert _raio_por_transporte("caminhando") == 1500

    def test_carro_amplia_raio(self):
        from services.roteiro_ia_service import _raio_por_transporte
        assert _raio_por_transporte("carro") == 10000
        assert _raio_por_transporte("moto") == 10000

    def test_transporte_publico_mantem_raio_padrao(self):
        from services.roteiro_ia_service import _raio_por_transporte
        assert _raio_por_transporte("ônibus") == 5000
        assert _raio_por_transporte(None) == 5000
