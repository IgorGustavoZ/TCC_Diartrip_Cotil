from fastapi import Cookie, HTTPException
from utils.security import decodificar_token
from database import get_db


def get_usuario_logado(access_token: str | None = Cookie(default=None)) -> int:
    if not access_token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    usuario_id = decodificar_token(access_token)
    
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT 1 FROM usuarios WHERE id_usuario = %s", (usuario_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")
        finally:
            cursor.close()
            
    return usuario_id
