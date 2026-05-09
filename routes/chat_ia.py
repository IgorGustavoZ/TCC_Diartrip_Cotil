from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import get_db
from utils.auth import get_usuario_logado
import anthropic
import os

router = APIRouter()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ChatInput(BaseModel):
    pergunta: str
    id_grupo: Optional[int] = None

@router.get("/chat")
def listar_chat(usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_chat, id_grupo, pergunta, resposta, data_interacao
            FROM chat_ia
            WHERE id_usuario = %s
            ORDER BY data_interacao DESC
            LIMIT 50
        """, (usuario_id,))
        dados = cursor.fetchall()
        cursor.close()
        return dados

@router.post("/chat")
def criar_chat(dados: ChatInput, usuario_id: int = Depends(get_usuario_logado)):
    if not dados.pergunta.strip():
        raise HTTPException(status_code=400, detail="Pergunta vazia")

    with get_db() as conexao:
        cursor = conexao.cursor()

        if dados.id_grupo:
            cursor.execute(
                "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
                (dados.id_grupo, usuario_id)
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=403, detail="Você não pertence ao grupo")

        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system="Você é um assistente especializado em planejamento de viagens. Responda sempre em português brasileiro. Seja objetivo e útil.",
                messages=[
                    {"role": "user", "content": dados.pergunta}
                ]
            )
            resposta = message.content[0].text
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Erro ao chamar a IA: {str(e)}")

        cursor.execute("""
            INSERT INTO chat_ia (id_usuario, id_grupo, pergunta, resposta)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, dados.id_grupo, dados.pergunta, resposta))
        conexao.commit()
        cursor.close()

    return {
        "pergunta": dados.pergunta,
        "resposta": resposta
    }