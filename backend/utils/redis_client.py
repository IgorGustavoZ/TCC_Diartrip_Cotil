"""
Cliente Redis com fallback transparente para memória.
Se REDIS_URL não estiver configurado ou o Redis estiver indisponível,
o sistema cai silenciosamente para os dicionários em memória
(funciona em dev/TCC; em produção real exige Redis).
"""
import os
import logging

logger = logging.getLogger("diartrip.redis")

_client = None
_tentou = False


def get_redis():
    """
    Retorna o cliente Redis ou None se indisponível.
    A conexão é lazy (criada na primeira chamada) e reutilizada.
    """
    global _client, _tentou
    if _tentou:
        return _client

    _tentou = True
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
            retry_on_timeout=False,
        )
        r.ping()
        _client = r
        logger.info("Redis conectado com sucesso.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis indisponível (%s) — usando fallback em memória.", exc)
        _client = None

    return _client
