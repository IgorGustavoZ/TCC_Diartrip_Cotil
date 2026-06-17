import jwt
import uuid
import secrets as _secrets_module
import threading
import logging
import time as _time_module
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import HTTPException
import os
from dotenv import load_dotenv
from utils.redis_client import get_redis, invalidar_redis

load_dotenv()

logger = logging.getLogger("diartrip.security")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não foi configurada nas variáveis de ambiente")

_ALGORITMOS_PERMITIDOS = {"HS256", "HS384", "HS512", "RS256", "RS384", "RS512"}
ALGORITHM = os.getenv("ALGORITHM", "HS256")
if ALGORITHM not in _ALGORITMOS_PERMITIDOS:
    raise RuntimeError(
        f"ALGORITHM '{ALGORITHM}' não é seguro. Use um destes: {sorted(_ALGORITMOS_PERMITIDOS)}"
    )
_ACCESS_TOKEN_LIFETIME = timedelta(minutes=30)
_REFRESH_TOKEN_TTL = 7 * 24 * 3600  # 7 dias em segundos
_IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

# Fallback em memória — APENAS para desenvolvimento local.
# Em produção o lifespan (main.py) aborta a inicialização sem Redis,
# mas se Redis cair pós-startup, as funções abaixo falham explicitamente.
_revogados: dict[str, float] = {}
_revogados_lock = threading.Lock()
# Refresh tokens em memória (dev only): token → (usuario_id, exp_timestamp)
_refresh_tokens_memory: dict[str, tuple[int, float]] = {}


def _limpar_revogados() -> None:
    agora = datetime.now(timezone.utc).timestamp()
    with _revogados_lock:
        for jti in list(_revogados.keys()):
            if _revogados[jti] < agora:
                del _revogados[jti]


def revogar_token(token: str) -> None:
    """Adiciona o JTI do token à blacklist no Redis (TTL automático).
    Em produção sem Redis: levanta 503 para não silenciar a falha de revogação.
    Em desenvolvimento: usa dicionário local como fallback."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = float(payload.get("exp", 0))
        if not jti:
            return
        ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
        r = get_redis()
        if r is not None:
            try:
                r.setex(f"bl:{jti}", ttl, "1")
            except Exception as redis_exc:
                invalidar_redis()
                if _IS_PRODUCTION:
                    logger.critical(
                        "Falha ao revogar token no Redis (conexão perdida). JTI=%s: %s", jti, redis_exc
                    )
                    raise HTTPException(
                        status_code=503,
                        detail="Serviço de autenticação temporariamente indisponível. Tente novamente.",
                    )
                logger.warning("Redis perdeu conexão pós-startup — revogando token em memória. JTI=%s", jti)
                _limpar_revogados()
                with _revogados_lock:
                    _revogados[jti] = exp
        elif _IS_PRODUCTION:
            logger.critical(
                "Redis indisponível em produção — revogação de token impossível. JTI=%s", jti
            )
            raise HTTPException(
                status_code=503,
                detail="Serviço de autenticação temporariamente indisponível. Tente novamente.",
            )
        else:
            logger.warning("Redis ausente — revogando token apenas em memória (dev only). JTI=%s", jti)
            _limpar_revogados()
            with _revogados_lock:
                _revogados[jti] = exp
    except HTTPException:
        raise
    except Exception:
        pass


def _is_revogado(jti: str) -> bool:
    """Verifica se o JTI está na blacklist.
    Em produção sem Redis: falha explicitamente para não aceitar tokens potencialmente revogados."""
    r = get_redis()
    if r is not None:
        try:
            return r.exists(f"bl:{jti}") > 0
        except Exception as redis_exc:
            invalidar_redis()
            if _IS_PRODUCTION:
                logger.critical(
                    "Falha ao verificar blacklist no Redis (conexão perdida). JTI=%s: %s", jti, redis_exc
                )
                raise HTTPException(
                    status_code=503,
                    detail="Serviço de autenticação temporariamente indisponível. Tente novamente.",
                )
            logger.warning("Redis perdeu conexão — checando blacklist em memória. JTI=%s", jti)
            with _revogados_lock:
                return jti in _revogados
    if _IS_PRODUCTION:
        logger.critical(
            "Redis indisponível em produção — não é possível verificar revogação. JTI=%s", jti
        )
        raise HTTPException(
            status_code=503,
            detail="Serviço de autenticação temporariamente indisponível. Tente novamente.",
        )
    with _revogados_lock:
        return jti in _revogados


def gerar_hash(senha: str) -> str:
    hashed = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verificar_senha(senha: str, hash_senha: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), hash_senha.encode("utf-8"))


def criar_token(usuario_id: int) -> str:
    jti = str(uuid.uuid4())
    exp = datetime.now(timezone.utc) + _ACCESS_TOKEN_LIFETIME
    payload = {"id": usuario_id, "jti": jti, "exp": exp}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── Refresh Token ─────────────────────────────────────────────────────────────

def criar_refresh_token(usuario_id: int) -> str:
    """Gera refresh token seguro e o armazena no Redis (ou memória em dev)."""
    token = _secrets_module.token_urlsafe(48)
    r = get_redis()
    if r is not None:
        r.setex(f"rt:{token}", _REFRESH_TOKEN_TTL, str(usuario_id))
    elif _IS_PRODUCTION:
        logger.critical("Redis indisponível — não é possível emitir refresh token em produção")
        raise HTTPException(status_code=503, detail="Serviço temporariamente indisponível.")
    else:
        exp = _time_module.time() + _REFRESH_TOKEN_TTL
        with _revogados_lock:
            _refresh_tokens_memory[token] = (usuario_id, exp)
    return token


def validar_e_revogar_refresh_token(token: str) -> int:
    """Valida refresh token, retorna usuario_id e o revoga atomicamente (rotação).
    Levanta 401 se o token for inválido ou expirado."""
    r = get_redis()
    if r is not None:
        pipe = r.pipeline()
        pipe.get(f"rt:{token}")
        pipe.delete(f"rt:{token}")
        results = pipe.execute()
        valor = results[0]
        if not valor:
            raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado. Faça login novamente.")
        return int(valor)
    elif _IS_PRODUCTION:
        logger.critical("Redis indisponível — não é possível validar refresh token em produção")
        raise HTTPException(status_code=503, detail="Serviço temporariamente indisponível.")
    else:
        with _revogados_lock:
            entry = _refresh_tokens_memory.pop(token, None)
        if not entry or _time_module.time() > entry[1]:
            raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado. Faça login novamente.")
        return entry[0]


def revogar_refresh_token(token: str) -> None:
    """Remove o refresh token (usado no logout)."""
    r = get_redis()
    if r is not None:
        r.delete(f"rt:{token}")
    elif not _IS_PRODUCTION:
        with _revogados_lock:
            _refresh_tokens_memory.pop(token, None)


def decodificar_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti", "")
        if jti and _is_revogado(jti):
            raise HTTPException(status_code=401, detail="Token revogado. Faça login novamente.")
        return payload["id"]
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
