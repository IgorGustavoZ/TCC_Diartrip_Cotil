import os
import logging
import threading
import time

logger = logging.getLogger("diartrip.redis")

_client = None
_lock = threading.Lock()
_ultima_tentativa: float = float("-inf")
_RETRY_INTERVAL: float = 30.0


def _conectar():
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
            health_check_interval=30,
        )
        r.ping()
        logger.info("Redis conectado com sucesso.")
        return r
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis indisponível (%s) — usando fallback em memória.", exc)
        return None


def get_redis():
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
    global _client, _ultima_tentativa
    with _lock:
        _client = None
        _ultima_tentativa = float("-inf")
    logger.warning("Cliente Redis invalidado — próxima operação tentará reconectar.")
