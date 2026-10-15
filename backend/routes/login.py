import logging
import os
import secrets

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from mysql.connector import IntegrityError
from pydantic import BaseModel

from schemas import LoginResponse, TokenResponse, MensagemResponse
from database import get_db
from services.email_verification_service import normalizar_email
from utils.security import (
    gerar_hash,
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
logger = logging.getLogger("diartrip.login_google")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
_EMISSORES_VALIDOS = ("accounts.google.com", "https://accounts.google.com")

_SECURE_COOKIES = os.getenv("ENVIRONMENT", "development") == "production"

_ACCESS_MAX_AGE = 30 * 60
_REFRESH_MAX_AGE = 7 * 24 * 3600


class LoginInput(BaseModel):
    email: str
    senha: str


def _set_auth_cookies(response: Response, usuario_id: int) -> None:
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
    verificar_rate_limit(f"login:{dados.email.strip().lower()}", limite=5)
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_usuario, senha_hash, email_verificado FROM usuarios WHERE email=%s",
                (dados.email,)
            )
            usuario = cursor.fetchone()
            if not usuario or not verificar_senha(dados.senha, usuario["senha_hash"]):
                raise HTTPException(status_code=401, detail="Informações inválidas")
            if not usuario.get("email_verificado", True):
                raise HTTPException(
                    status_code=403,
                    detail="Email ainda nao verificado. Confirme o codigo enviado para sua caixa de entrada.",
                )
            _set_auth_cookies(response, usuario["id_usuario"])
            return {"mensagem": "Login realizado com sucesso", "usuario_id": usuario["id_usuario"]}
        finally:
            cursor.close()


class GoogleLoginInput(BaseModel):
    credential: str


def _verificar_credencial_google(credential: str) -> dict:
    """Valida o token de identidade do Google (assinatura, audiência, emissor,
    expiração) usando a biblioteca oficial — nunca decodifica o JWT "na mão"
    e nunca confia em dados enviados separadamente pelo frontend. Levanta
    HTTPException(401) com mensagem genérica em qualquer falha; o motivo
    real só vai pro log do servidor."""
    if not GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID não configurado — login com Google indisponível")
        raise HTTPException(status_code=503, detail="Login com Google não está disponível no momento")

    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    try:
        claims = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), audience=GOOGLE_CLIENT_ID
        )
    except Exception as exc:
        logger.warning("Token do Google rejeitado: %s", exc)
        raise HTTPException(status_code=401, detail="Token do Google inválido ou expirado")

    # verify_oauth2_token já valida o emissor internamente, mas conferimos
    # de novo aqui explicitamente — e-mail/sub ausentes também invalidam o
    # token pro nosso uso, mesmo que a assinatura em si seja válida.
    if claims.get("iss") not in _EMISSORES_VALIDOS:
        raise HTTPException(status_code=401, detail="Token do Google inválido")
    if not claims.get("sub") or not claims.get("email"):
        raise HTTPException(status_code=401, detail="Token do Google inválido")
    if not claims.get("email_verified"):
        raise HTTPException(status_code=401, detail="O e-mail desta conta Google não foi verificado")

    return claims


@router.post("/google", response_model=LoginResponse)
def login_google(dados: GoogleLoginInput, request: Request, response: Response):
    verificar_rate_limit(f"login_google:{request.client.host if request.client else 'desconhecido'}", limite=20)

    claims = _verificar_credencial_google(dados.credential)
    google_sub = claims["sub"]
    email = normalizar_email(claims["email"])
    nome = (claims.get("name") or email.split("@")[0]).strip()[:100] or "Usuário"
    foto = (claims.get("picture") or None)
    if foto:
        foto = foto[:250]

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            # Cenário A: conta já vinculada a este identificador Google.
            cursor.execute("SELECT id_usuario FROM usuarios WHERE google_sub=%s", (google_sub,))
            usuario = cursor.fetchone()
            if usuario:
                usuario_id = usuario["id_usuario"]
            else:
                # Cenário C: o e-mail já pertence a uma conta local (ou outra
                # conta Google, que nunca deveria compartilhar e-mail com
                # esta) ainda não vinculada — não cria duplicata nem vincula
                # automaticamente. Sem um fluxo de vinculação autenticado
                # implementado ainda, orienta a pessoa a entrar com a senha.
                cursor.execute("SELECT id_usuario FROM usuarios WHERE email=%s", (email,))
                existente = cursor.fetchone()
                if existente:
                    raise HTTPException(
                        status_code=409,
                        detail="Este e-mail já possui uma conta Diartrip. Entre com sua senha para acessar.",
                    )

                # Cenário B: primeiro acesso com Google. A senha é um hash
                # aleatório que nenhuma senha real jamais vai bater — evita
                # alterar a constraint NOT NULL de senha_hash só pra isso.
                # email_verificado=1 direto: o Google já afirma que o
                # e-mail é verificado, não faz sentido repetir o fluxo de
                # código por e-mail do cadastro tradicional.
                senha_hash_aleatoria = gerar_hash(secrets.token_urlsafe(32))
                try:
                    cursor.execute(
                        """INSERT INTO usuarios
                               (nome, email, senha_hash, google_sub, foto_perfil, email_verificado)
                           VALUES (%s, %s, %s, %s, %s, 1)""",
                        (nome, email, senha_hash_aleatoria, google_sub, foto),
                    )
                    usuario_id = cursor.lastrowid
                except IntegrityError as exc:
                    if exc.errno != 1062:
                        raise
                    # Corrida: duas requisições quase simultâneas tentando
                    # criar a mesma conta Google — a outra já ganhou, só
                    # reaproveita o que ela criou em vez de falhar ou duplicar.
                    cursor.execute(
                        "SELECT id_usuario FROM usuarios WHERE google_sub=%s OR email=%s",
                        (google_sub, email),
                    )
                    usuario = cursor.fetchone()
                    if not usuario:
                        raise
                    usuario_id = usuario["id_usuario"]
        finally:
            cursor.close()

    _set_auth_cookies(response, usuario_id)
    return {"mensagem": "Login realizado com sucesso", "usuario_id": usuario_id}


@router.post("/token/refresh", response_model=TokenResponse)
def token_refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
):
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
