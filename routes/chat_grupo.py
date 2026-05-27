from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from database import get_db
from utils.auth import get_usuario_logado
from utils.dependencies import checar_membro_grupo
from utils.security import decodificar_token
from utils.rate_limiter import verificar_rate_limit
from utils.ws_manager import manager
from services import chat_grupo_service

router = APIRouter(tags=["Chat Grupo"])


class MensagemInput(BaseModel):
    conteudo: str = Field(..., min_length=1, max_length=2000)


@router.get("/grupos/{id_grupo}/chat")
def listar_mensagens(
    id_grupo: int,
    since_id: int = Query(0),
    usuario_id: int = Depends(get_usuario_logado),
):
    return chat_grupo_service.listar(id_grupo, usuario_id, since_id)


@router.post("/grupos/{id_grupo}/chat")
def enviar_mensagem(
    id_grupo: int, dados: MensagemInput, usuario_id: int = Depends(get_usuario_logado)
):
    return chat_grupo_service.enviar(id_grupo, usuario_id, dados.conteudo)


@router.websocket("/grupos/{id_grupo}/chat/ws")
async def chat_websocket(ws: WebSocket, id_grupo: int):
    token = ws.cookies.get("access_token")
    if not token:
        await ws.close(code=1008)
        return

    try:
        usuario_id = decodificar_token(token)
    except HTTPException:
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

            with get_db() as conexao:
                cursor = conexao.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO mensagens_grupo (id_grupo, id_usuario, conteudo) VALUES (%s, %s, %s)",
                        (id_grupo, usuario_id, conteudo),
                    )
                    conexao.commit()
                    id_mensagem = cursor.lastrowid
                finally:
                    cursor.close()

            await manager.broadcast(id_grupo, {
                "id_mensagem": id_mensagem,
                "id_usuario": usuario_id,
                "nome": usuario_nome,
                "foto_perfil": usuario_foto,
                "conteudo": conteudo,
                "data_envio": datetime.now(timezone.utc).isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnect(ws, id_grupo)
    except Exception:
        manager.disconnect(ws, id_grupo)
