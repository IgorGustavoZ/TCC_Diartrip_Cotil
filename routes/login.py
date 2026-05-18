from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db
from utils.security import verificar_senha, criar_token

router = APIRouter()

class LoginInput(BaseModel):
    email: str
    senha: str

@router.post("/login")
def login(dados: LoginInput):
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
            usuario_id = usuario["id_usuario"]
            token = criar_token(usuario_id)
            return {
                "mensagem": "Login realizado com sucesso",
                "usuario_id": usuario_id,
                "token": token
            }
        finally:
            cursor.close()