"""test_custos_viagem.py — Custos da viagem (opções salvas via SerpApi,
fluxo salva -> orçamento -> paga/descartada)."""
from unittest.mock import MagicMock, patch

from tests.conftest import fake_get_db, make_connection, make_cursor

OPCAO_VOO_PAYLOAD = {
    "tipo": "voo", "nome": "LATAM", "origem": "GRU", "destino": "CDG",
    "data_ida": "2027-01-10", "data_volta": "2027-01-20", "preco": 3500.0,
}

OPCAO_HOSPEDAGEM_PAYLOAD = {
    "tipo": "hospedagem", "nome": "Hotel Teste", "destino": "Paris",
    "data_ida": "2027-01-10", "data_volta": "2027-01-20", "preco": 900.0,
}


def _conn_opcao(fetchones):
    # Sequência simples de fetchone (autenticação / cargo / linha da opção),
    # sem fetchall — usada pelos endpoints que agem sobre UMA opção.
    fetch_idx = [0]

    def factory(**kw):
        c = MagicMock()
        c.rowcount = 1

        def _fetchone():
            i = fetch_idx[0]
            fetch_idx[0] += 1
            return fetchones[i] if i < len(fetchones) else None

        c.fetchone.side_effect = _fetchone
        c.fetchall.return_value = []
        return c

    conn = MagicMock()
    conn.cursor.side_effect = factory
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


class TestSalvarOpcaoCusto:
    def test_membro_pode_salvar_opcao_de_voo(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/custos", json=OPCAO_VOO_PAYLOAD)
        assert resp.status_code == 201

    def test_membro_pode_salvar_opcao_de_hospedagem(self, client_usuario):
        cur = make_cursor(rows=[(1,), {"cargo": "membro"}])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/custos", json=OPCAO_HOSPEDAGEM_PAYLOAD)
        assert resp.status_code == 201

    def test_nao_membro_nao_pode_salvar(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/custos", json=OPCAO_VOO_PAYLOAD)
        assert resp.status_code == 403

    def test_tipo_invalido_retorna_422(self, client_usuario):
        payload = dict(OPCAO_VOO_PAYLOAD, tipo="carro")
        resp = client_usuario.post("/grupos/10/custos", json=payload)
        assert resp.status_code == 422

    def test_preco_negativo_retorna_422(self, client_usuario):
        payload = dict(OPCAO_VOO_PAYLOAD, preco=-10)
        resp = client_usuario.post("/grupos/10/custos", json=payload)
        assert resp.status_code == 422

    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/grupos/10/custos", json=OPCAO_VOO_PAYLOAD)
        assert resp.status_code == 401


class TestListarOpcoesCusto:
    def test_membro_pode_listar(self, client_usuario):
        linhas = [{
            "id_opcao": 1, "id_grupo": 10, "id_usuario": 1, "tipo": "voo", "status": "salva",
            "nome": "LATAM", "origem": "GRU", "destino": "CDG", "data_ida": "2027-01-10",
            "data_volta": "2027-01-20", "preco": "3500.00", "moeda": "BRL", "link_externo": None,
            "detalhes": None, "data_consulta": "2027-01-01 10:00:00", "id_gasto": None,
            "data_criacao": "2027-01-01 10:00:00",
        }]
        fetch_idx = [0]
        fetchones = [(1,), {"cargo": "membro"}]

        def factory(**kw):
            c = MagicMock()

            def _fetchone():
                i = fetch_idx[0]
                fetch_idx[0] += 1
                return fetchones[i] if i < len(fetchones) else None

            c.fetchone.side_effect = _fetchone
            c.fetchall.return_value = linhas
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/custos")
        assert resp.status_code == 200
        assert resp.json()[0]["nome"] == "LATAM"
        assert resp.json()[0]["preco"] == 3500.0

    def test_nao_membro_nao_pode_listar(self, client_usuario):
        cur = make_cursor(rows=[(1,), None])
        conn = make_connection(cur)
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.get("/grupos/10/custos")
        assert resp.status_code == 403

    def test_listar_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/grupos/10/custos")
        assert resp.status_code == 401


_OPCAO_BASE = {"id_opcao": 1, "id_grupo": 10, "tipo": "voo", "nome": "LATAM", "detalhes": None}


class TestAdicionarAoOrcamento:
    def test_membro_pode_adicionar_opcao_salva_ao_orcamento(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="salva", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.patch("/grupos/10/custos/1/orcamento")
        assert resp.status_code == 200

    def test_opcao_de_outro_grupo_retorna_404(self, client_usuario):
        opcao = dict(_OPCAO_BASE, id_grupo=99, status="salva", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.patch("/grupos/10/custos/1/orcamento")
        assert resp.status_code == 404

    def test_opcao_ja_paga_nao_pode_voltar_pro_orcamento(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="paga", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.patch("/grupos/10/custos/1/orcamento")
        assert resp.status_code == 400

    def test_nao_membro_nao_pode_adicionar(self, client_usuario):
        conn = _conn_opcao([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.patch("/grupos/10/custos/1/orcamento")
        assert resp.status_code == 403


class TestDescartarOpcaoCusto:
    def test_membro_pode_descartar(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="orcamento", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.patch("/grupos/10/custos/1/descartar")
        assert resp.status_code == 200

    def test_nao_pode_descartar_opcao_ja_paga(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="paga", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.patch("/grupos/10/custos/1/descartar")
        assert resp.status_code == 400


class TestExcluirOpcaoCusto:
    def test_membro_pode_excluir_opcao_nao_paga(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="salva", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/grupos/10/custos/1")
        assert resp.status_code == 200

    def test_nao_pode_excluir_opcao_ja_paga(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="paga", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/grupos/10/custos/1")
        assert resp.status_code == 400

    def test_opcao_de_outro_grupo_retorna_404(self, client_usuario):
        opcao = dict(_OPCAO_BASE, id_grupo=99, status="salva", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.delete("/grupos/10/custos/1")
        assert resp.status_code == 404


class TestPagarOpcaoCusto:
    def test_voo_marca_pago_com_categoria_transporte(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="orcamento", preco="3500.00", tipo="voo")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.custo_viagem_service.gasto_service.criar",
                   return_value={"mensagem": "ok", "id": 77}) as mock_criar:
            resp = client_usuario.post("/grupos/10/custos/1/pagar", json={})
        assert resp.status_code == 200
        assert resp.json()["id_gasto"] == 77
        dados_passados = mock_criar.call_args.args[2]
        assert dados_passados.categoria == "transporte"
        assert dados_passados.valor == 3500.0

    def test_hospedagem_marca_pago_com_categoria_hospedagem(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="salva", preco="900.00", tipo="hospedagem", nome="Hotel X")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.custo_viagem_service.gasto_service.criar",
                   return_value={"mensagem": "ok", "id": 78}) as mock_criar:
            resp = client_usuario.post("/grupos/10/custos/1/pagar", json={})
        assert resp.status_code == 200
        dados_passados = mock_criar.call_args.args[2]
        assert dados_passados.categoria == "hospedagem"

    def test_valor_customizado_sobrescreve_preco_salvo(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="salva", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.custo_viagem_service.gasto_service.criar",
                   return_value={"mensagem": "ok", "id": 79}) as mock_criar:
            resp = client_usuario.post("/grupos/10/custos/1/pagar", json={"valor": 150.0})
        assert resp.status_code == 200
        dados_passados = mock_criar.call_args.args[2]
        assert dados_passados.valor == 150.0

    def test_opcao_ja_paga_retorna_409_sem_criar_gasto(self, client_usuario):
        # Impede que cliques/requisições repetidas gerem um segundo gasto:
        # o status já marcado como 'paga' é detectado antes de qualquer
        # chamada a gasto_service.criar().
        opcao = dict(_OPCAO_BASE, status="paga", preco="3500.00")
        conn = _conn_opcao([(1,), {"cargo": "membro"}, opcao])
        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.custo_viagem_service.gasto_service.criar") as mock_criar:
            resp = client_usuario.post("/grupos/10/custos/1/pagar", json={})
        assert resp.status_code == 409
        mock_criar.assert_not_called()

    def test_falha_ao_criar_gasto_reverte_status_da_opcao(self, client_usuario):
        opcao = dict(_OPCAO_BASE, status="orcamento", preco="3500.00")
        fetchones = [(1,), {"cargo": "membro"}, opcao]
        fetch_idx = [0]
        execucoes = []

        def factory(**kw):
            c = MagicMock()
            c.rowcount = 1

            def _fetchone():
                i = fetch_idx[0]
                fetch_idx[0] += 1
                return fetchones[i] if i < len(fetchones) else None

            def _execute(sql, params=None):
                execucoes.append((sql, params))

            c.fetchone.side_effect = _fetchone
            c.fetchall.return_value = []
            c.execute.side_effect = _execute
            return c

        conn = MagicMock()
        conn.cursor.side_effect = factory
        conn.commit = MagicMock()
        conn.rollback = MagicMock()
        conn.close = MagicMock()

        with patch("database.get_db", fake_get_db(conn)), \
             patch("services.custo_viagem_service.gasto_service.criar",
                   side_effect=RuntimeError("falha simulada")):
            resp = client_usuario.post("/grupos/10/custos/1/pagar", json={})

        # A falha no gasto_service propaga (500), mas antes disso o código
        # emite um UPDATE que volta a opção pro status anterior ('orcamento')
        # em vez de deixá-la travada em 'paga' sem gasto nenhum vinculado.
        assert resp.status_code == 500
        assert any(e[1] == ("orcamento", 1) for e in execucoes if "SET status=%s" in e[0])

    def test_nao_membro_nao_pode_pagar(self, client_usuario):
        conn = _conn_opcao([(1,), None])
        with patch("database.get_db", fake_get_db(conn)):
            resp = client_usuario.post("/grupos/10/custos/1/pagar", json={})
        assert resp.status_code == 403

    def test_pagar_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/grupos/10/custos/1/pagar", json={})
        assert resp.status_code == 401


class TestResumoFinanceiro:
    def test_resumo_combina_orcamento_existente_e_opcoes_planejadas(self, client_usuario):
        with patch("services.custo_viagem_service.dashboard_service.geral", return_value={
            "nome_grupo": "Viagem", "orcamento_total": 10000.0, "total_consumido": 2000.0,
            "orcamento_restante": 8000.0, "percentual_consumido": 20.0,
            "distribuicao_categorias": [
                {"categoria": "transporte", "total": 500.0, "qtd": 1},
                {"categoria": "hospedagem", "total": 1500.0, "qtd": 1},
            ],
        }):
            cur = make_cursor(rows=[(1,)])
            cur.fetchall.return_value = [{"tipo": "voo", "total": 3500.0}, {"tipo": "hospedagem", "total": 900.0}]
            conn = make_connection(cur)
            with patch("database.get_db", fake_get_db(conn)):
                resp = client_usuario.get("/grupos/10/custos/resumo-financeiro")
        assert resp.status_code == 200
        corpo = resp.json()
        assert corpo["orcamento_total"] == 10000.0
        assert corpo["planejado_voos"] == 3500.0
        assert corpo["planejado_hospedagem"] == 900.0
        assert corpo["gastos_categoria_transporte"] == 500.0
        assert corpo["gastos_categoria_hospedagem"] == 1500.0
