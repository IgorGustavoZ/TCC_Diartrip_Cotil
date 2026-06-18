import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from schemas import MensagemGrupoResponse
from database import get_db
from utils.auth import get_usuario_logado
from utils.dependencies import checar_membro_grupo
from utils.security import decodificar_token
from utils.rate_limiter import verificar_rate_limit
from utils.ws_manager import manager
from services import chat_grupo_service

logger = logging.getLogger("diartrip.chat_grupo")
router = APIRouter(tags=["Chat Grupo"])

_WS_REAUTH_INTERVALO = 20


class MensagemInput(BaseModel):
    conteudo: str = Field(..., min_length=1, max_length=2000)


def _origem_permitida(ws: WebSocket) -> bool:
    origin = ws.headers.get("origin")
    if origin is None:
        return True
    allowed = {
        o.strip().lower().rstrip("/")
        for o in os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000").split(",")
        if o.strip()
    }
    return origin.lower().rstrip("/") in allowed


@router.get("/grupos/{id_grupo}/chat", response_model=list[MensagemGrupoResponse])
def listar_mensagens(
    id_grupo: int,
    since_id: int = Query(0, ge=0),
    usuario_id: int = Depends(get_usuario_logado),
):
    return chat_grupo_service.listar(id_grupo, usuario_id, since_id)


@router.post("/grupos/{id_grupo}/chat", response_model=MensagemGrupoResponse)
async def enviar_mensagem(
    id_grupo: int, dados: MensagemInput, usuario_id: int = Depends(get_usuario_logado)
):
    msg = chat_grupo_service.enviar(id_grupo, usuario_id, dados.conteudo)

    data_envio_str = (
        msg["data_envio"].isoformat()
        if hasattr(msg.get("data_envio"), "isoformat")
        else str(msg.get("data_envio", ""))
    )
    await manager.broadcast(id_grupo, {
        "id_mensagem": msg["id_mensagem"],
        "id_grupo":    id_grupo,
        "id_usuario":  msg["id_usuario"],
        "nome":        msg["nome"],
        "foto_perfil": msg["foto_perfil"],
        "conteudo":    msg["conteudo"],
        "data_envio":  data_envio_str,
    })
    return msg


@router.websocket("/grupos/{id_grupo}/chat/ws")
async def chat_websocket(ws: WebSocket, id_grupo: int, token_query: str | None = Query(None, alias="token")):
    if not _origem_permitida(ws):
        await ws.close(code=1008)
        return

    token = ws.cookies.get("access_token") or token_query
    if not token:
        logger.warning("WS conexão recusada: token ausente (grupo=%s)", id_grupo)
        await ws.close(code=1008)
        return

    try:
        usuario_id = decodificar_token(token)
    except HTTPException:
        logger.warning("WS conexão recusada: token inválido (grupo=%s)", id_grupo)
        await ws.close(code=1008)
        return

    usuario_nome = ""
    usuario_foto = None

    try:
        with get_db() as conexao:
            cursor = conexao.cursor(dictionary=True)
            try:
                checar_membro_grupo(cursor, id_grupo, usuario_id)
                cursor.execute(
                    "SELECT nome, foto_perfil FROM usuarios WHERE id_usuario=%s",
                    (usuario_id,),
                )
                u = cursor.fetchone()
                if u:
                    usuario_nome = u["nome"]
                    usuario_foto = u.get("foto_perfil")
            finally:
                cursor.close()
    except HTTPException:
        await ws.close(code=1008)
        return

    await manager.connect(ws, id_grupo)
    mensagens_count = 0
    try:
        while True:
            data = await ws.receive_json()
            conteudo = str(data.get("conteudo", "")).strip()
            if not conteudo or len(conteudo) > 2000:
                continue

            try:
                verificar_rate_limit(f"chat:{usuario_id}", limite=30)
            except HTTPException:
                await ws.send_json({"erro": "Muitas mensagens. Aguarde um momento."})
                continue

            mensagens_count += 1
            if mensagens_count % _WS_REAUTH_INTERVALO == 0:
                try:
                    with get_db() as conn_check:
                        cur_check = conn_check.cursor(dictionary=True)
                        try:
                            checar_membro_grupo(cur_check, id_grupo, usuario_id)
                        finally:
                            cur_check.close()
                except HTTPException:
                    await ws.send_json({"erro": "Você não pertence mais a este grupo."})
                    await ws.close(code=1008)
                    manager.disconnect(ws, id_grupo)
                    return

            with get_db() as conexao:
                cursor = conexao.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO mensagens_grupo (id_grupo, id_usuario, conteudo) VALUES (%s, %s, %s)",
                        (id_grupo, usuario_id, conteudo),
                    )
                    id_mensagem = cursor.lastrowid
                finally:
                    cursor.close()

            await manager.broadcast(id_grupo, {
                "id_mensagem": id_mensagem,
                "id_grupo":    id_grupo,
                "id_usuario":  usuario_id,
                "nome":        usuario_nome,
                "foto_perfil": usuario_foto,
                "conteudo":    conteudo,
                "data_envio":  datetime.now(timezone.utc).isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnect(ws, id_grupo)
    except Exception:
        manager.disconnect(ws, id_grupo)
