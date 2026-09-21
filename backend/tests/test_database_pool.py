"""Regressão: conexões mortas no pool travavam o login por ~20 s.

O pool do mysql-connector faz ping antes de entregar cada conexão, dentro de
um lock global. Conexão morta (PC suspenso, rede caiu) = ping pendurado. O
database.py agora (1) usa timeouts, (2) recria o pool ocioso antes do uso e
(3) recria o pool se obter conexão falhar ou demorar.
"""
import queue
import time

import pytest

import database


class FakePool:
    """Pool falso com fila real (o fechamento em segundo plano drena _cnx_queue)."""

    def __init__(self, conexao=None, erro=None):
        self._cnx_queue = queue.Queue()
        self._conexao = conexao
        self._erro = erro
        self.pedidos = 0

    def get_connection(self):
        self.pedidos += 1
        if self._erro is not None:
            raise self._erro
        return self._conexao


@pytest.fixture
def estado_do_pool():
    """Restaura o estado global do módulo (o conftest injeta um pool falso)."""
    salvo = (database._pool, database._pool_criado_aqui, database._ultimo_uso)
    yield
    database._pool, database._pool_criado_aqui, database._ultimo_uso = salvo


def test_pool_injetado_nunca_e_reciclado(estado_do_pool):
    injetado = FakePool()
    database._pool = injetado
    database._pool_criado_aqui = None  # não foi criado pelo módulo (caso dos testes)
    database._ultimo_uso = time.time() - 10_000
    assert database._get_pool() is injetado


def test_pool_ocioso_e_recriado_antes_do_uso(estado_do_pool, monkeypatch):
    velho, novo = FakePool(), FakePool()
    database._pool = velho
    database._pool_criado_aqui = velho
    database._ultimo_uso = time.time() - 10_000
    monkeypatch.setattr(database, "_criar_pool", lambda: novo)

    assert database._get_pool() is novo
    assert database._pool is novo


def test_pool_em_uso_recente_e_mantido(estado_do_pool, monkeypatch):
    atual = FakePool()
    database._pool = atual
    database._pool_criado_aqui = atual
    database._ultimo_uso = time.time()
    monkeypatch.setattr(database, "_criar_pool", lambda: pytest.fail("não deveria recriar"))

    assert database._get_pool() is atual


def test_pool_nasce_uma_unica_vez(estado_do_pool, monkeypatch):
    database._pool = None
    database._pool_criado_aqui = None
    criados = []

    def criar():
        criados.append(FakePool())
        return criados[-1]

    monkeypatch.setattr(database, "_criar_pool", criar)
    a, b = database._get_pool(), database._get_pool()
    assert a is b and len(criados) == 1


def test_falha_ao_obter_conexao_recria_pool_e_tenta_de_novo(estado_do_pool, monkeypatch):
    conexao = object()
    quebrado = FakePool(erro=RuntimeError("conexão morta"))
    saudavel = FakePool(conexao=conexao)
    database._pool = quebrado
    database._pool_criado_aqui = quebrado
    database._ultimo_uso = time.time()
    monkeypatch.setattr(database, "_criar_pool", lambda: saudavel)

    assert database._obter_conexao() is conexao
    assert database._pool is saudavel
    assert quebrado.pedidos == 1


def test_falha_persistente_propaga_o_erro(estado_do_pool, monkeypatch):
    quebrado = FakePool(erro=RuntimeError("banco fora do ar"))
    database._pool = quebrado
    database._pool_criado_aqui = quebrado
    database._ultimo_uso = time.time()
    monkeypatch.setattr(database, "_criar_pool", lambda: FakePool(erro=RuntimeError("banco fora do ar")))

    with pytest.raises(RuntimeError, match="banco fora do ar"):
        database._obter_conexao()


def test_obter_conexao_lento_descarta_o_pool_mas_entrega_a_conexao(estado_do_pool, monkeypatch):
    conexao = object()
    lento = FakePool(conexao=conexao)
    database._pool = lento
    database._pool_criado_aqui = lento
    database._ultimo_uso = time.time()
    monkeypatch.setattr(database, "_OBTER_LENTO_SEG", -1)  # qualquer demora conta como lenta

    assert database._obter_conexao() is conexao
    assert database._pool is None  # próxima requisição cria um pool novo


def test_invalidar_so_atinge_o_pool_que_deu_problema(estado_do_pool):
    velho, atual = FakePool(), FakePool()
    database._pool = atual
    database._pool_criado_aqui = atual

    database._invalidar_pool(velho)  # outra thread já trocou o pool: não derruba o novo
    assert database._pool is atual

    database._invalidar_pool(atual)
    assert database._pool is None


def test_timeouts_do_pool_configuraveis_e_com_padrao_seguro(monkeypatch):
    monkeypatch.delenv("DB_TIMEOUT_SEG", raising=False)
    assert database._env_inteiro("DB_TIMEOUT_SEG", 8, 2, 120) == 8
    monkeypatch.setenv("DB_TIMEOUT_SEG", "15")
    assert database._env_inteiro("DB_TIMEOUT_SEG", 8, 2, 120) == 15
    monkeypatch.setenv("DB_TIMEOUT_SEG", "abc")
    assert database._env_inteiro("DB_TIMEOUT_SEG", 8, 2, 120) == 8
    monkeypatch.setenv("DB_TIMEOUT_SEG", "9999")
    assert database._env_inteiro("DB_TIMEOUT_SEG", 8, 2, 120) == 8
