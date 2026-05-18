from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import get_db
from utils.auth import get_usuario_logado
from openai import OpenAI
import os

router = APIRouter()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

class ChatInput(BaseModel):
    pergunta: str
    id_grupo: int


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
def criar_chat(
    dados: ChatInput,
    usuario_id: int = Depends(get_usuario_logado)
):

    if not dados.pergunta.strip():
        raise HTTPException(
            status_code=400,
            detail="Pergunta vazia"
        )

    with get_db() as conexao:

        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (dados.id_grupo, usuario_id)
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=403,
                detail="Você não pertence ao grupo"
            )

        cursor.execute("""
            SELECT nome_grupo, destino_principal, data_inicio, data_fim
            FROM grupos_viagem
            WHERE id_grupo=%s
        """, (dados.id_grupo,))

        grupo = cursor.fetchone()

        cursor.execute("""
            SELECT pergunta, resposta
            FROM chat_ia
            WHERE id_usuario=%s AND id_grupo=%s
            ORDER BY data_interacao ASC
            LIMIT 10
        """, (usuario_id, dados.id_grupo))

        conversas = cursor.fetchall()

        historico = []

        for item in conversas:

            historico.append({
                "role": "user",
                "content": item["pergunta"]
            })

            historico.append({
                "role": "assistant",
                "content": item["resposta"]
            })

        historico.append({
            "role": "user",
            "content": dados.pergunta
        })

        try:

            resposta_ia = client.chat.completions.create(

                model="openrouter/free",

                messages=[
                    {
                        "role": "system",
                        "content": f"""
                        Você é um assistente especializado em planejamento de viagens.

                        Informações da viagem:

                        Nome da viagem:
                        {grupo['nome_grupo']}

                        Destino:
                        {grupo['destino_principal']}

                        Data de início:
                        {grupo['data_inicio']}

                        Data de fim:
                        {grupo['data_fim']}

                        Regras:
                        - Responda sempre em português brasileiro
                        - Seja objetivo e útil
                        - Dê sugestões práticas
                        - Organize respostas quando necessário
                        - Considere o contexto da viagem
                        """
                    },

                    *historico
                ],

                max_tokens=1024
            )

            resposta = resposta_ia.choices[0].message.content

        except Exception as e:

            raise HTTPException(
                status_code=502,
                detail=f"Erro ao chamar IA: {str(e)}"
            )

        cursor.execute("""
            INSERT INTO chat_ia (id_usuario, id_grupo, pergunta, resposta)
            VALUES (%s, %s, %s, %s)
        """, (
            usuario_id,
            dados.id_grupo,
            dados.pergunta,
            resposta
        ))

        conexao.commit()

        cursor.close()

    return {
        "pergunta": dados.pergunta,
        "resposta": resposta
    }