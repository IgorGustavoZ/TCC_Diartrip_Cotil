import time
import threading
from fastapi import HTTPException
from utils.redis_client import get_redis

_lock = threading.Lock()
_janelas: dict[str, list[float]] = {}

MAX_REQUISICOES = 10
JANELA_SEGUNDOS = 60


def _verificar_redis(r, chave: str, limite: int) -> None:
    agora = time.time()
    corte = agora - JANELA_SEGUNDOS
    key = f"rl:{chave}"

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, "-inf", corte)
    pipe.zadd(key, {str(agora): agora})
    pipe.zcard(key)
    pipe.expire(key, JANELA_SEGUNDOS + 1)
    results = pipe.execute()

    contagem = results[2]
    if contagem > limite:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas. Aguarde um momento e tente novamente.",
        )


def _verificar_memoria(chave: str, limite: int) -> None:
    agora = time.monotonic()
    corte = agora - JANELA_SEGUNDOS

    with _lock:
        if len(_janelas) > 10000:
            for k in list(_janelas.keys()):
                _janelas[k] = [t for t in _janelas[k] if t > corte]
                if not _janelas[k]:
                    del _janelas[k]

        historico = _janelas.get(chave, [])
        historico = [t for t in historico if t > corte]

        if len(historico) >= limite:
            raise HTTPException(
                status_code=429,
                detail="Muitas tentativas. Aguarde um momento e tente novamente.",
            )

        historico.append(agora)
        _janelas[chave] = historico


def verificar_rate_limit(chave: str | int, limite: int = MAX_REQUISICOES) -> None:
    chave = str(chave)
    r = get_redis()
    if r is not None:
        _verificar_redis(r, chave, limite)
    else:
        _verificar_memoria(chave, limite)
