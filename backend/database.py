import mysql.connector
from mysql.connector import pooling
import os
import logging
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("diartrip.database")

_pool = None

_POOL_SIZE_MIN = 1
_POOL_SIZE_MAX = 32
_POOL_SIZE_DEFAULT = 10


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


def _get_pool():
    global _pool
    if _pool is None:
        tamanho = _resolver_pool_size()
        logger.info("Iniciando pool MySQL com %d conexões.", tamanho)
        _pool = pooling.MySQLConnectionPool(
            pool_name="diartrip_pool",
            pool_size=tamanho,
            pool_reset_session=True,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
    return _pool


@contextmanager
def get_db():
    conexao = _get_pool().get_connection()
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()
