import time
import threading
from fastapi import HTTPException

_lock = threading.Lock()
_janelas: dict[int, list[float]] = {}

MAX_REQUISICOES = 10
JANELA_SEGUNDOS = 60


def verificar_rate_limit(chave: str | int, limite: int = MAX_REQUISICOES) -> None:
    agora = time.monotonic()
    corte = agora - JANELA_SEGUNDOS

    with _lock:
        # Mecanismo de limpeza para evitar vazamento de memória
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
