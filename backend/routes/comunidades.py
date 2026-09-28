from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from schemas import ComunidadeResponse, ComunidadeCriada, MensagemResponse
from utils.auth import get_usuario_logado
from utils.rate_limiter import verificar_rate_limit
from services import comunidade_service

router = APIRouter()


class ComunidadeInput(BaseModel):
    nome: str = Field(..., min_length=3, max_length=150)
    descricao: Optional[str] = Field(None, max_length=2000)
    categoria: Optional[str] = Field(None, max_length=100)
    privacidade: str = Field("publica", pattern="^(publica|privada)$")


@router.post("/comunidades", response_model=ComunidadeCriada, status_code=201)
def criar_comunidade(dados: ComunidadeInput, usuario_id: int = Depends(get_usuario_logado)):
    verificar_rate_limit(f"criar_comunidade:{usuario_id}", limite=10)
    return comunidade_service.criar(
        usuario_id, dados.nome, dados.descricao, dados.categoria, dados.privacidade
    )


@router.get("/comunidades", response_model=list[ComunidadeResponse])
def listar_comunidades(
    busca: str | None = Query(None, max_length=150),
    limite: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"buscar_comunidades:{usuario_id}", limite=30)
    return comunidade_service.listar(usuario_id, busca, limite, offset)


@router.get("/comunidades/{id_comunidade}", response_model=ComunidadeResponse)
def detalhar_comunidade(id_comunidade: int, usuario_id: int = Depends(get_usuario_logado)):
    return comunidade_service.detalhar(id_comunidade, usuario_id)


@router.post("/comunidades/{id_comunidade}/entrar", response_model=MensagemResponse)
def entrar_comunidade(id_comunidade: int, usuario_id: int = Depends(get_usuario_logado)):
    verificar_rate_limit(f"entrar_comunidade:{usuario_id}", limite=20)
    return comunidade_service.entrar(id_comunidade, usuario_id)


@router.delete("/comunidades/{id_comunidade}/sair", response_model=MensagemResponse)
def sair_comunidade(id_comunidade: int, usuario_id: int = Depends(get_usuario_logado)):
    return comunidade_service.sair(id_comunidade, usuario_id)
