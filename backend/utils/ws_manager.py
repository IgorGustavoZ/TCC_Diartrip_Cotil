import logging
from collections import defaultdict
from fastapi import WebSocket

logger = logging.getLogger("diartrip.ws")


class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, ws: WebSocket, id_grupo: int) -> None:
        await ws.accept()
        self._connections[id_grupo].append(ws)
        logger.info("WS conectado: grupo=%s total=%s", id_grupo, len(self._connections[id_grupo]))

    def disconnect(self, ws: WebSocket, id_grupo: int) -> None:
        try:
            self._connections[id_grupo].remove(ws)
            if not self._connections[id_grupo]:
                del self._connections[id_grupo]
        except (ValueError, KeyError):
            pass
        logger.info("WS desconectado: grupo=%s", id_grupo)

    async def broadcast(self, id_grupo: int, message: dict) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(id_grupo, [])):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, id_grupo)


manager = ConnectionManager()
