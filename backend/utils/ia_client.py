"""Cliente compartilhado de IA (OpenRouter).

Único ponto de configuração do client OpenAI/OpenRouter do projeto — usado
pelo chat da viagem (services/chat_service.py) e pela geração de roteiro por
IA (services/roteiro_ia_service.py). Não criar um segundo client em outro
lugar do projeto.
"""
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
IA_MODEL = os.getenv("IA_MODEL", "mistralai/mistral-7b-instruct:free")
