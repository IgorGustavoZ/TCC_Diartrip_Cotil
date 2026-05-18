from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo
from utils.rate_limiter import verificar_rate_limit
from openai import OpenAI
import os

_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
IA_MODEL = os.getenv("IA_MODEL", "mistralai/mistral-7b-instruct:free")


def listar(usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT id_chat, id_grupo, pergunta, resposta, data_interacao
                FROM chat_ia
                WHERE id_usuario = %s
                ORDER BY data_interacao DESC
                LIMIT 50
                """,
                (usuario_id,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def criar(pergunta: str, id_grupo: int, usuario_id: int) -> dict:
    verificar_rate_limit(usuario_id)

    if not pergunta.strip():
        raise HTTPException(status_code=400, detail="Pergunta vazia")

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)

            cursor.execute(
                """
                SELECT nome_grupo, destino_principal, data_inicio, data_fim,
                       orcamento, tipo_viagem
                FROM grupos_viagem
                WHERE id_grupo=%s
                """,
                (id_grupo,),
            )
            grupo = cursor.fetchone()

            cursor.execute(
                """
                SELECT pergunta, resposta
                FROM chat_ia
                WHERE id_usuario=%s AND id_grupo=%s
                ORDER BY data_interacao ASC
                LIMIT 10
                """,
                (usuario_id, id_grupo),
            )
            historico = []
            for item in cursor.fetchall():
                historico.append({"role": "user", "content": item["pergunta"]})
                historico.append({"role": "assistant", "content": item["resposta"]})
            historico.append({"role": "user", "content": pergunta})

            try:
                resposta_ia = _client.chat.completions.create(
                    model=IA_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Você é um assistente de viagens eficiente.\n\n"
                                f"Contexto:\n"
                                f"- Nome: {grupo.get('nome_grupo', 'N/A')}\n"
                                f"- Destino: {grupo.get('destino_principal', 'N/A')}\n"
                                f"- Tipo: {grupo.get('tipo_viagem', 'N/A')}\n"
                                f"- Orçamento: R$ {grupo.get('orcamento', '0')}\n"
                                f"- Período: {grupo.get('data_inicio')} a {grupo.get('data_fim')}\n\n"
                                "Regras:\n"
                                "- Responda em Português Brasileiro.\n"
                                "- Seja direto. Use listas para roteiros.\n"
                                "- Se o roteiro for longo, foque nos destaques para evitar cortes."
                            ),
                        },
                        *historico,
                    ],
                    max_tokens=2048,
                )
                resposta = resposta_ia.choices[0].message.content
            except Exception:
                raise HTTPException(status_code=502, detail="Serviço de IA indisponível. Tente novamente.")

            cursor2 = conexao.cursor()
            cursor2.execute(
                "INSERT INTO chat_ia (id_usuario, id_grupo, pergunta, resposta) VALUES (%s, %s, %s, %s)",
                (usuario_id, id_grupo, pergunta, resposta),
            )
            conexao.commit()
            cursor2.close()

        finally:
            cursor.close()

    return {"pergunta": pergunta, "resposta": resposta}
