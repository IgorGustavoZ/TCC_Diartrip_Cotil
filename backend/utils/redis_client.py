"""
Cliente Redis com fallback transparente para memória.

Comportamento:
- REDIS_URL ausente → fallback em memória (dev/TCC).
- Redis indisponível no startup → retry a cada 30s.
- Redis cai após conexão → health_check_interval reconecta automaticamente.
- Operação falha mesmo com _client != None → invalidar_redis() permite retry.

Múltiplos workers:
- Cada worker uvicorn tem seu próprio _client (conexão separada ao mesmo Redis).
- Em produção com múltiplos workers, o fallback em memória NÃO é compartilhado.
  O lifespan em main.py aborta startup em produção se Redis não estiver disponível.

Persistência recomendada (produção):
- Habilite RDB + AOF no Redis para sobreviver a restarts.
  redis.conf: appendonly yes
               save 900 1 / save 300 10 / save 60 10000
"""
import os
import logging
import threading
import time

logger = logging.getLogger("diartrip.redis")

_client = None
_lock = threading.Lock()
_ultima_tentativa: float = float("-inf")  # sentinela: nunca tentou → sempre tenta na 1ª chamada
_RETRY_INTERVAL: float = 30.0            # segundos entre tentativas após falha


def _conectar():
    """Tenta criar e pingar um cliente Redis com health_check_interval."""
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        logger.info("REDIS_URL não configurado — usando fallback em memória.")
        return None
    try:
        import redis  # noqa: PLC0415
        r = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True,
            # Envia PING periódico para detectar e reconectar conexões obsoletas.
            # Essencial para workers de longa duração (produção/uvicorn).
            health_check_interval=30,
        )
        r.ping()
        logger.info("Redis conectado com sucesso.")
        return r
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis indisponível (%s) — usando fallback em memória.", exc)
        return None


def get_redis():
    """
    Retorna o cliente Redis ou None se indisponível.
    - Lazy: conecta na primeira chamada.
    - Retry: tenta reconectar após _RETRY_INTERVAL s se falhou anteriormente.
    - Thread-safe: usa lock para evitar múltiplas conexões simultâneas.
    """
    global _client, _ultima_tentativa

    if _client is not None:
        return _client

    agora = time.monotonic()
    with _lock:
        if _client is not None:
            return _client
        if agora - _ultima_tentativa < _RETRY_INTERVAL:
            return None
        _ultima_tentativa = agora
        _client = _conectar()

    return _client


def invalidar_redis() -> None:
    """Marca o cliente Redis como inválido para forçar reconexão na próxima chamada.

    Deve ser chamado quando uma operação Redis falha com erro de conexão,
    indicando que o cliente em cache está obsoleto (ex: Redis reiniciou).
    O próximo get_redis() tentará reconectar respeitando _RETRY_INTERVAL.
    """
    global _client, _ultima_tentativa
    with _lock:
        _client = None
        _ultima_tentativa = float("-inf")  # Permite retry imediato na próxima chamada
    logger.warning("Cliente Redis invalidado — próxima operação tentará reconectar.")
