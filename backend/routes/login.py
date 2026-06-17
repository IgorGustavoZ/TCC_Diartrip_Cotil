import os
from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel
from schemas import LoginResponse, TokenResponse, MensagemResponse
from database import get_db
from utils.security import (
    verificar_senha,
    criar_token,
    revogar_token,
    criar_refresh_token,
    validar_e_revogar_refresh_token,
    revogar_refresh_token,
)
from utils.rate_limiter import verificar_rate_limit
from utils.csrf import gerar_csrf_token

router = APIRouter()

_SECURE_COOKIES = os.getenv("ENVIRONMENT", "development") == "production"

_ACCESS_MAX_AGE = 30 * 60
_REFRESH_MAX_AGE = 7 * 24 * 3600


class LoginInput(BaseModel):
    email: str
    senha: str


def _set_auth_cookies(response: Response, usuario_id: int) -> None:
    """Emite access_token + refresh_token + csrf_token como cookies."""
    access = criar_token(usuario_id)
    refresh = criar_refresh_token(usuario_id)
    csrf = gerar_csrf_token()

    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        samesite="lax",
        max_age=_ACCESS_MAX_AGE,
        secure=_SECURE_COOKIES,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        samesite="lax",
        max_age=_REFRESH_MAX_AGE,
        secure=_SECURE_COOKIES,
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf,
        httponly=False,
        samesite="lax",
        max_age=_ACCESS_MAX_AGE,
        secure=_SECURE_COOKIES,
    )


@router.post("/login", response_model=LoginResponse)
def login(dados: LoginInput, response: Response):
    verificar_rate_limit(f"login:{dados.email}", limite=5)
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_usuario, senha_hash FROM usuarios WHERE email=%s",
                (dados.email,)
            )
            usuario = cursor.fetchone()
            if not usuario or not verificar_senha(dados.senha, usuario["senha_hash"]):
                raise HTTPException(status_code=401, detail="Informações inválidas")
            _set_auth_cookies(response, usuario["id_usuario"])
            return {"mensagem": "Login realizado com sucesso", "usuario_id": usuario["id_usuario"]}
        finally:
            cursor.close()


@router.post("/token/refresh", response_model=TokenResponse)
def token_refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
):
    """Renova access_token usando refresh_token (rotação automática).
    Isento de CSRF — o refresh_token HttpOnly+SameSite=Strict é a proteção."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token ausente. Faça login novamente.")

    usuario_id = validar_e_revogar_refresh_token(refresh_token)

    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT 1 FROM usuarios WHERE id_usuario=%s", (usuario_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=401, detail="Usuário não encontrado.")
        finally:
            cursor.close()

    _set_auth_cookies(response, usuario_id)
    return {"mensagem": "Token renovado com sucesso"}


@router.post("/logout", response_model=MensagemResponse)
def logout(
    response: Response,
    access_token: str | None = Cookie(default=None),
    refresh_token: str | None = Cookie(default=None),
):
    if access_token:
        revogar_token(access_token)
    if refresh_token:
        revogar_refresh_token(refresh_token)

    for key in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(
            key=key,
            httponly=(key != "csrf_token"),
            samesite="strict",
            secure=_SECURE_COOKIES,
        )
    return {"mensagem": "Logout realizado"}
