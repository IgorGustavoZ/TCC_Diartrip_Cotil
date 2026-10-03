import time
import threading
from fastapi import HTTPException
from utils.redis_client import get_redis

_lock = threading.Lock()
_janelas: dict[str, list[float]] = {}

MAX_REQUISICOES = 10
JANELA_SEGUNDOS = 60
_MAIOR_JANELA = 24 * 3600


def _verificar_redis(r, chave: str, limite: int, janela: int = JANELA_SEGUNDOS) -> None:
    agora = time.time()
    corte = agora - janela
    key = f"rl:{chave}"

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, "-inf", corte)
    pipe.zadd(key, {str(agora): agora})
    pipe.zcard(key)
    pipe.expire(key, janela + 1)
    results = pipe.execute()

    contagem = results[2]
    if contagem > limite:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas. Aguarde um momento e tente novamente.",
        )


def _verificar_memoria(chave: str, limite: int, janela: int = JANELA_SEGUNDOS) -> None:
    agora = time.monotonic()
    corte = agora - janela

    with _lock:
        if len(_janelas) > 10000:
            # Limpeza usa a maior janela possível para não apagar o histórico
            # de chaves com janela longa (ex.: limites por hora)
            corte_limpeza = agora - _MAIOR_JANELA
            for k in list(_janelas.keys()):
                _janelas[k] = [t for t in _janelas[k] if t > corte_limpeza]
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


def verificar_rate_limit(
    chave: str | int, limite: int = MAX_REQUISICOES, janela: int = JANELA_SEGUNDOS
) -> None:
    chave = str(chave)
    janela = min(janela, _MAIOR_JANELA)
    r = get_redis()
    if r is not None:
        _verificar_redis(r, chave, limite, janela)
    else:
        _verificar_memoria(chave, limite, janela)
