"""Cliente compartilhado de IA (OpenRouter), com backup automático.

Único ponto de configuração do client OpenAI/OpenRouter do projeto — usado
pelo chat da viagem (services/chat_service.py) e pela geração de roteiro por
IA (services/roteiro_ia_service.py). Não criar um segundo client em outro
lugar do projeto.

`client` expõe a mesma interface do SDK (`client.chat.completions.create`),
mas, se a chamada principal falhar, tenta em ordem:

    1. IA_MODELOS_BACKUP  → outros modelos no próprio OpenRouter, separados
       por vírgula (ex.: "meta-llama/llama-3.3-70b-instruct:free,...");
    2. IA_BACKUP_BASE_URL + IA_BACKUP_API_KEY + IA_BACKUP_MODEL → um segundo
       provedor compatível com a API da OpenAI (ex.: Groq, Together, um
       Ollama local em http://localhost:11434/v1).

Nada configurado = comportamento idêntico ao original (só o OpenRouter).
Se tudo falhar, relança o erro do provedor PRINCIPAL — assim a detecção de
"sem créditos" (402) em roteiro_ia_service continua funcionando.

IA_FORCAR_BACKUP=true pula o provedor principal (útil para testar o backup).
"""
import os
import logging
from openai import OpenAI, APIConnectionError, APIStatusError

logger = logging.getLogger("diartrip.ia_client")

IA_MODEL = os.getenv("IA_MODEL", "mistralai/mistral-7b-instruct:free")

_principal = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

_BACKUP_TIMEOUT = float(os.getenv("IA_BACKUP_TIMEOUT", "60"))


def _criar_backup() -> tuple[OpenAI, str] | None:
    base_url = os.getenv("IA_BACKUP_BASE_URL")
    modelo = os.getenv("IA_BACKUP_MODEL")
    if not base_url or not modelo:
        return None
    # Ollama local não exige key, mas o SDK exige uma string não vazia
    api_key = os.getenv("IA_BACKUP_API_KEY") or "sem-key"
    return OpenAI(base_url=base_url, api_key=api_key, timeout=_BACKUP_TIMEOUT), modelo


_backup = _criar_backup()


# Só vale a pena tentar outro modelo/provedor quando o erro é de
# disponibilidade: sem créditos (402), modelo inexistente/fora do ar (404),
# timeout (408), rate limit (429) ou erro do servidor (5xx). Erros da própria
# requisição (400, 401, 403, 422 — ex.: conteúdo bloqueado pela moderação)
# falhariam igual nos backups, só multiplicando custo e espalhando o prompt
# (com dados do usuário) para mais provedores.
_STATUS_COM_FALLBACK = {402, 404, 408, 429}


def _vale_tentar_backup(exc: Exception) -> bool:
    if isinstance(exc, APIConnectionError):  # inclui APITimeoutError
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code in _STATUS_COM_FALLBACK or exc.status_code >= 500
    return False


def _modelos_backup_openrouter() -> list[str]:
    return [m.strip() for m in os.getenv("IA_MODELOS_BACKUP", "").split(",") if m.strip()]


class _CompletionsComFallback:
    def create(self, **kwargs):
        modelo_pedido = kwargs.pop("model", IA_MODEL)

        # (descrição para log, client, modelo)
        tentativas: list[tuple[str, OpenAI, str]] = []
        if os.getenv("IA_FORCAR_BACKUP", "false").strip().lower() != "true":
            tentativas.append(("OpenRouter principal", _principal, modelo_pedido))
        for modelo in _modelos_backup_openrouter():
            if modelo != modelo_pedido:
                tentativas.append(("OpenRouter backup", _principal, modelo))
        if _backup is not None:
            tentativas.append(("provedor IA secundário", _backup[0], _backup[1]))

        if not tentativas:
            raise RuntimeError("IA_FORCAR_BACKUP=true, mas nenhum backup de IA está configurado")

        primeiro_erro: Exception | None = None
        for descricao, cliente, modelo in tentativas:
            try:
                resposta = cliente.chat.completions.create(model=modelo, **kwargs)
                if primeiro_erro is not None:
                    logger.info("IA respondeu via %s (modelo %s)", descricao, modelo)
                return resposta
            except Exception as exc:
                logger.warning("IA falhou em %s (modelo %s): %s", descricao, modelo, exc)
                if primeiro_erro is None:
                    primeiro_erro = exc
                if not _vale_tentar_backup(exc):
                    break
        raise primeiro_erro


class _ChatComFallback:
    def __init__(self):
        self.completions = _CompletionsComFallback()


class _ClienteIAComFallback:
    """Mesma interface usada do SDK OpenAI; qualquer outro atributo é
    repassado ao client principal, então nada que já existia quebra."""

    def __init__(self):
        self.chat = _ChatComFallback()

    def __getattr__(self, nome):
        return getattr(_principal, nome)


client = _ClienteIAComFallback()
