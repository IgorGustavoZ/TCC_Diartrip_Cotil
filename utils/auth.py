from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from utils.security import decodificar_token

security = HTTPBearer()

def get_usuario_logado(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    usuario_id = decodificar_token(token)
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return usuario_id