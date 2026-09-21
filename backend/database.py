import mysql.connector
from mysql.connector import pooling
import os
import queue
import threading
import time
import logging
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("diartrip.database")

_pool = None
_pool_lock = threading.Lock()
# Pool criado por ESTE módulo (os testes injetam um pool falso em _pool e ele
# nunca deve ser reciclado) e o instante do último uso dele.
_pool_criado_aqui = None
_ultimo_uso = 0.0

_POOL_SIZE_MIN = 1
_POOL_SIZE_MAX = 32
_POOL_SIZE_DEFAULT = 10

# Conexões ociosas podem morrer sem aviso (PC suspenso, rede/VPN caiu, firewall
# do banco). O pool do mysql-connector faz um "ping" antes de entregar cada
# conexão, dentro de um lock GLOBAL: uma conexão morta trava o acesso ao banco
# de TODAS as requisições por ~20 s (o timeout de TCP), uma conexão por vez —
# o app estoura o timeout e o login falha. Três proteções:
#   1. timeouts de conexão/leitura/escrita: o ping numa conexão morta falha
#      rápido em vez de esperar o TCP desistir;
#   2. pool ocioso por muito tempo é recriado ANTES do uso (cobre suspensão);
#   3. se obter uma conexão falhar ou demorar, o pool inteiro é recriado.
_TIMEOUT_SEG_DEFAULT = 8
_IDLE_RECICLAR_SEG_DEFAULT = 120
_OBTER_LENTO_SEG = 3.0


def _resolver_pool_size() -> int:
    raw = os.getenv("DB_POOL_SIZE", str(_POOL_SIZE_DEFAULT)).strip()
    try:
        tamanho = int(raw)
    except ValueError:
        logger.warning(
            "DB_POOL_SIZE='%s' não é um inteiro válido — usando padrão %d.",
            raw, _POOL_SIZE_DEFAULT,
        )
        return _POOL_SIZE_DEFAULT

    if tamanho < _POOL_SIZE_MIN or tamanho > _POOL_SIZE_MAX:
        logger.warning(
            "DB_POOL_SIZE=%d fora do intervalo [%d, %d] — usando padrão %d.",
            tamanho, _POOL_SIZE_MIN, _POOL_SIZE_MAX, _POOL_SIZE_DEFAULT,
        )
        return _POOL_SIZE_DEFAULT

    return tamanho


def _env_inteiro(nome: str, padrao: int, minimo: int, maximo: int) -> int:
    raw = os.getenv(nome, str(padrao)).strip()
    try:
        valor = int(raw)
    except ValueError:
        logger.warning("%s='%s' não é um inteiro válido — usando padrão %d.", nome, raw, padrao)
        return padrao
    if valor < minimo or valor > maximo:
        logger.warning(
            "%s=%d fora do intervalo [%d, %d] — usando padrão %d.",
            nome, valor, minimo, maximo, padrao,
        )
        return padrao
    return valor


def _criar_pool():
    tamanho = _resolver_pool_size()
    timeout = _env_inteiro("DB_TIMEOUT_SEG", _TIMEOUT_SEG_DEFAULT, 2, 120)
    logger.info("Iniciando pool MySQL com %d conexões (timeout %ds).", tamanho, timeout)
    return pooling.MySQLConnectionPool(
        pool_name="diartrip_pool",
        pool_size=tamanho,
        pool_reset_session=True,
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        connection_timeout=timeout,
        read_timeout=timeout,
        write_timeout=timeout,
    )


def _fechar_pool_em_segundo_plano(pool) -> None:
    """Fecha as conexões de um pool descartado sem bloquear nenhuma requisição
    (desconectar uma conexão morta pode demorar). Drena a fila diretamente para
    não disputar o lock global do mysql-connector com o pool novo."""
    def _fechar():
        fila = getattr(pool, "_cnx_queue", None)
        if fila is None:
            return
        while True:
            try:
                cnx = fila.get(block=False)
            except queue.Empty:
                break
            try:
                cnx.disconnect()
            except Exception:
                pass

    threading.Thread(target=_fechar, name="db-pool-close", daemon=True).start()


def _descartar_pool_locked() -> None:
    global _pool, _pool_criado_aqui
    velho, _pool = _pool, None
    _pool_criado_aqui = None
    if velho is not None:
        _fechar_pool_em_segundo_plano(velho)


def _invalidar_pool(pool_com_problema) -> None:
    # Só descarta se o pool atual ainda é o que deu problema: várias requisições
    # podem detectar a mesma falha ao mesmo tempo e não devem derrubar, em
    # cadeia, o pool novo que outra thread acabou de criar.
    with _pool_lock:
        if _pool is pool_com_problema:
            _descartar_pool_locked()


def _get_pool():
    global _pool, _pool_criado_aqui, _ultimo_uso
    with _pool_lock:
        agora = time.time()
        if (
            _pool is not None
            and _pool is _pool_criado_aqui
            and _ultimo_uso
            and agora - _ultimo_uso > _env_inteiro(
                "DB_IDLE_RECICLAR_SEG", _IDLE_RECICLAR_SEG_DEFAULT, 10, 86400
            )
        ):
            logger.warning(
                "Pool MySQL sem uso há %.0fs (PC suspenso ou rede caiu?) — "
                "recriando para não entregar conexões mortas.",
                agora - _ultimo_uso,
            )
            _descartar_pool_locked()
        # O lock também protege a criação: sem ele, várias requisições
        # simultâneas na partida criavam um pool cada (N x conexões).
        if _pool is None:
            _pool = _criar_pool()
            _pool_criado_aqui = _pool
        if _pool is _pool_criado_aqui:
            _ultimo_uso = agora
        return _pool


def _obter_conexao():
    pool = _get_pool()
    inicio = time.monotonic()
    try:
        conexao = pool.get_connection()
    except Exception as exc:
        logger.warning(
            "Falha ao obter conexão do pool (%s) — recriando o pool e tentando de novo.", exc
        )
        _invalidar_pool(pool)
        return _get_pool().get_connection()

    demora = time.monotonic() - inicio
    if demora > _OBTER_LENTO_SEG:
        logger.warning(
            "Obter conexão levou %.1fs (havia conexão morta no pool) — recriando o pool.", demora
        )
        _invalidar_pool(pool)
    return conexao


@contextmanager
def get_db():
    conexao = _obter_conexao()
    try:
        yield conexao
        conexao.commit()
    except Exception:
        try:
            conexao.rollback()
        except Exception as exc:
            logger.warning("Falha no rollback (conexão possivelmente morta): %s", exc)
        raise
    finally:
        try:
            conexao.close()
        except Exception as exc:
            logger.warning("Falha ao devolver a conexão ao pool: %s", exc)
