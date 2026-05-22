from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, EmailStr, Field, field_validator
from utils.auth import get_usuario_logado
from utils.rate_limiter import verificar_rate_limit
from services import usuario_service

router = APIRouter(tags=["Usuários"])

_MAX_FOTO_BYTES = 5 * 1024 * 1024
_SENHAS_PROIBIDAS = {
    "password123", "12345678", "123456789", "qwerty123",
    "senha123", "diartrip123", "abc12345", "iloveyou1",
}


class UsuarioInput(BaseModel):
    nome: str = Field(..., max_length=100)
    email: EmailStr = Field(..., max_length=150)
    senha: str = Field(..., min_length=8, max_length=100)

    @field_validator("senha")
    @classmethod
    def senha_forte(cls, v: str) -> str:
        if v.lower() in _SENHAS_PROIBIDAS:
            raise ValueError("Senha muito comum. Escolha uma mais segura.")
        if not any(c.isupper() for c in v):
            raise ValueError("A senha deve conter ao menos uma letra maiúscula.")
        if not any(c.isdigit() for c in v):
            raise ValueError("A senha deve conter ao menos um número.")
        return v


class UsuarioUpdate(BaseModel):
    nome: str = Field(..., max_length=100)
    email: EmailStr = Field(..., max_length=150)
    bio: str | None = Field(None, max_length=500)


@router.get("/usuarios/me")
def obter_perfil_atual(usuario_id: int = Depends(get_usuario_logado)):
    return usuario_service.buscar_por_id(usuario_id)


@router.get("/usuarios/{id_usuario}")
def buscar_usuario(id_usuario: int, _: int = Depends(get_usuario_logado)):
    return usuario_service.buscar_por_id_publico(id_usuario)


@router.post("/usuarios")
def criar_usuario(dados: UsuarioInput):
    verificar_rate_limit(f"cadastro:{dados.email}", limite=5)
    return usuario_service.criar(dados.nome, dados.email, dados.senha)


@router.patch("/usuarios/{id_usuario}/foto")
async def atualizar_foto_usuario(
    id_usuario: int,
    foto: UploadFile = File(...),
    usuario_logado: int = Depends(get_usuario_logado),
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    conteudo = await foto.read(_MAX_FOTO_BYTES + 1)
    if len(conteudo) > _MAX_FOTO_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Máximo 5 MB.")
    return usuario_service.atualizar_foto(id_usuario, foto.filename or "perfil.jpg", conteudo)


@router.put("/usuarios/{id_usuario}")
def atualizar_usuario(
    id_usuario: int,
    dados: UsuarioUpdate,
    usuario_logado: int = Depends(get_usuario_logado),
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return usuario_service.atualizar(id_usuario, dados.nome, dados.email, dados.bio)


@router.delete("/usuarios/{id_usuario}")
def deletar_usuario(
    id_usuario: int, usuario_logado: int = Depends(get_usuario_logado)
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return usuario_service.deletar(id_usuario)
