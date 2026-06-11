import mysql.connector
from mysql.connector import pooling
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="diartrip_pool",
            pool_size=10,
            pool_reset_session=True,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
    return _pool


@contextmanager
def get_db():
    """
    Retira uma conexão do pool, cede ao bloco 'with' e a devolve ao pool.
    Em caso de erro, faz rollback automático antes de devolver.
    """
    conexao = _get_pool().get_connection()
    try:
        yield conexao
        conexao.commit()        
    except Exception:
        conexao.rollback()      
        raise
    finally:
        conexao.close()         