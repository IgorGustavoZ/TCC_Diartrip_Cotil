from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from typing import Optional
from schemas import ComunidadeResponse, ComunidadeCriada, CodigoConviteResponse, FotoComunidadeResponse, MensagemResponse
from utils.auth import get_usuario_logado
from utils.rate_limiter import verificar_rate_limit
from services import comunidade_service

router = APIRouter()

_MAX_FOTO_BYTES = 5 * 1024 * 1024


class ComunidadeInput(BaseModel):
    nome: str = Field(..., min_length=3, max_length=150)
    descricao: Optional[str] = Field(None, max_length=2000)
    categoria: Optional[str] = Field(None, max_length=100)
    privacidade: str = Field("publica", pattern="^(publica|privada)$")


class EntrarComunidadeInput(BaseModel):
    codigo: Optional[str] = Field(None, max_length=10)


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


@router.put("/comunidades/{id_comunidade}", response_model=MensagemResponse)
def atualizar_comunidade(
    id_comunidade: int, dados: ComunidadeInput, usuario_id: int = Depends(get_usuario_logado)
):
    return comunidade_service.atualizar(
        id_comunidade, usuario_id, dados.nome, dados.descricao, dados.categoria, dados.privacidade
    )


@router.get("/comunidades/{id_comunidade}/codigo-convite", response_model=CodigoConviteResponse)
def obter_codigo_convite_comunidade(id_comunidade: int, usuario_id: int = Depends(get_usuario_logado)):
    return comunidade_service.obter_codigo_convite(id_comunidade, usuario_id)


@router.patch("/comunidades/{id_comunidade}/foto", response_model=FotoComunidadeResponse)
async def atualizar_foto_comunidade(
    id_comunidade: int,
    foto: UploadFile = File(...),
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"foto_comunidade:{usuario_id}", limite=10)
    conteudo = await foto.read(_MAX_FOTO_BYTES + 1)
    if len(conteudo) > _MAX_FOTO_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Máximo 5 MB.")
    return comunidade_service.atualizar_foto(id_comunidade, usuario_id, foto.filename or "capa.jpg", conteudo)


@router.post("/comunidades/{id_comunidade}/entrar", response_model=MensagemResponse)
def entrar_comunidade(
    id_comunidade: int, dados: EntrarComunidadeInput = EntrarComunidadeInput(),
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"entrar_comunidade:{usuario_id}", limite=20)
    return comunidade_service.entrar(id_comunidade, usuario_id, dados.codigo)


@router.delete("/comunidades/{id_comunidade}/sair", response_model=MensagemResponse)
def sair_comunidade(id_comunidade: int, usuario_id: int = Depends(get_usuario_logado)):
    return comunidade_service.sair(id_comunidade, usuario_id)
