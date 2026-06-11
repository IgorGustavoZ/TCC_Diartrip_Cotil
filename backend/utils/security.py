import jwt
import uuid
import threading
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import HTTPException
import os
from dotenv import load_dotenv
from utils.redis_client import get_redis

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não foi configurada nas variáveis de ambiente")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
_TOKEN_EXPIRE_HOURS = 2

# Fallback em memória quando Redis não está disponível (jti → timestamp expiração)
_revogados: dict[str, float] = {}
_revogados_lock = threading.Lock()


def _limpar_revogados() -> None:
    agora = datetime.now(timezone.utc).timestamp()
    with _revogados_lock:
        for jti in list(_revogados.keys()):
            if _revogados[jti] < agora:
                del _revogados[jti]


def revogar_token(token: str) -> None:
    """Adiciona o JTI do token à blacklist (Redis com TTL, ou memória como fallback)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = float(payload.get("exp", 0))
        if not jti:
            return
        ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
        r = get_redis()
        if r is not None:
            r.setex(f"bl:{jti}", ttl, "1")
        else:
            _limpar_revogados()
            with _revogados_lock:
                _revogados[jti] = exp
    except Exception:
        pass


def _is_revogado(jti: str) -> bool:
    r = get_redis()
    if r is not None:
        return r.exists(f"bl:{jti}") > 0
    with _revogados_lock:
        return jti in _revogados


def gerar_hash(senha: str) -> str:
    hashed = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verificar_senha(senha: str, hash_senha: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), hash_senha.encode("utf-8"))


def criar_token(usuario_id: int) -> str:
    jti = str(uuid.uuid4())
    exp = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    payload = {"id": usuario_id, "jti": jti, "exp": exp}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


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
