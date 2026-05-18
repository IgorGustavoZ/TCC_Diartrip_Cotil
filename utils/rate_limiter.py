import time
import threading
from fastapi import HTTPException

_lock = threading.Lock()
_janelas: dict[int, list[float]] = {}

MAX_REQUISICOES = 10
JANELA_SEGUNDOS = 60


def verificar_rate_limit(usuario_id: int) -> None:
    agora = time.monotonic()
    corte = agora - JANELA_SEGUNDOS

    with _lock:
        historico = _janelas.get(usuario_id, [])
        historico = [t for t in historico if t > corte]

        if len(historico) >= MAX_REQUISICOES:
            raise HTTPException(
                status_code=429,
                detail=f"Limite de {MAX_REQUISICOES} mensagens por minuto atingido. Aguarde.",
            )

        historico.append(agora)
        _janelas[usuario_id] = historico
