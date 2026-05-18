from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from utils.auth import get_usuario_logado
from services import usuario_service

router = APIRouter(tags=["Usuários"])


class UsuarioInput(BaseModel):
    nome: str
    email: EmailStr
    senha: str


class UsuarioUpdate(BaseModel):
    nome: str
    email: EmailStr


@router.get("/usuarios/me")
def obter_perfil_atual(usuario_id: int = Depends(get_usuario_logado)):
    return usuario_service.buscar_por_id(usuario_id)


@router.get("/usuarios/{id_usuario}")
def buscar_usuario(id_usuario: int, _: int = Depends(get_usuario_logado)):
    return usuario_service.buscar_por_id(id_usuario)


@router.post("/usuarios")
def criar_usuario(dados: UsuarioInput):
    return usuario_service.criar(dados.nome, dados.email, dados.senha)


@router.put("/usuarios/{id_usuario}")
def atualizar_usuario(
    id_usuario: int,
    dados: UsuarioUpdate,
    usuario_logado: int = Depends(get_usuario_logado),
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return usuario_service.atualizar(id_usuario, dados.nome, dados.email)


@router.delete("/usuarios/{id_usuario}")
def deletar_usuario(
    id_usuario: int, usuario_logado: int = Depends(get_usuario_logado)
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return usuario_service.deletar(id_usuario)
