import os
from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel
from database import get_db
from utils.security import verificar_senha, criar_token, revogar_token
from utils.rate_limiter import verificar_rate_limit

router = APIRouter()

# Em produção (ENVIRONMENT=production), o cookie só trafega em HTTPS.
_SECURE_COOKIES = os.getenv("ENVIRONMENT", "development") == "production"


class LoginInput(BaseModel):
    email: str
    senha: str


@router.post("/login")
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
            token = criar_token(usuario["id_usuario"])
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                samesite="strict",
                max_age=7200,
                secure=_SECURE_COOKIES,
            )
            return {"mensagem": "Login realizado com sucesso", "usuario_id": usuario["id_usuario"]}
        finally:
            cursor.close()


@router.post("/logout")
def logout(response: Response, access_token: str | None = Cookie(default=None)):
    if access_token:
        revogar_token(access_token)
    response.delete_cookie("access_token")
    return {"mensagem": "Logout realizado"}
