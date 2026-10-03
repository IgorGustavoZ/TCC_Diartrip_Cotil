from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, Response, UploadFile, File
from pydantic import BaseModel, EmailStr, Field, field_validator
from schemas import (
    UsuarioDesktop, UsuarioPublico, UsuarioMe, UsuarioCriado, UsuarioSimples,
    FotoPerfilResponse, SeguirResponse, MensagemResponse, LoginResponse,
    UsuarioAtualizadoResponse,
)
from utils.auth import get_usuario_logado
from utils.rate_limiter import verificar_rate_limit
from utils.security import revogar_token, revogar_refresh_token
from routes.login import _set_auth_cookies
from services import usuario_service
from services import email_verification_service
from services.email_verification_service import EmailDeliveryError, normalizar_email

router = APIRouter(tags=["Usuários"])

_MAX_FOTO_BYTES = 5 * 1024 * 1024
_SENHAS_PROIBIDAS = {
    "password123", "12345678", "123456789", "qwerty123",
    "senha123", "diartrip123", "abc12345", "iloveyou1",
}


def _validar_senha_forte(v: str) -> str:
    if v.lower() in _SENHAS_PROIBIDAS:
        raise ValueError("Senha muito comum. Escolha uma mais segura.")
    if not any(c.isupper() for c in v):
        raise ValueError("A senha deve conter ao menos uma letra maiúscula.")
    if not any(c.isdigit() for c in v):
        raise ValueError("A senha deve conter ao menos um número.")
    return v


class UsuarioInput(BaseModel):
    nome: str = Field(..., max_length=100)
    email: EmailStr = Field(..., max_length=150)
    senha: str = Field(..., min_length=8, max_length=100)

    @field_validator("senha")
    @classmethod
    def senha_forte(cls, v: str) -> str:
        return _validar_senha_forte(v)


class UsuarioUpdate(BaseModel):
    nome: str = Field(..., max_length=100)
    email: EmailStr = Field(..., max_length=150)
    bio: str | None = Field(None, max_length=500)


class TrocarSenhaInput(BaseModel):
    senha_atual: str = Field(..., min_length=1, max_length=100)
    nova_senha: str = Field(..., min_length=8, max_length=100)

    @field_validator("nova_senha")
    @classmethod
    def nova_senha_forte(cls, v: str) -> str:
        return _validar_senha_forte(v)


class VerificarEmailInput(BaseModel):
    email: EmailStr
    codigo: str = Field(..., pattern=r"^\d{6}$")
    senha: str = Field(..., min_length=1, max_length=100)


class ReenviarCodigoInput(BaseModel):
    email: EmailStr


class ConfirmarEmailInput(BaseModel):
    codigo: str = Field(..., pattern=r"^\d{6}$")


def _ip(request: Request) -> str:
    return request.client.host if request.client else "desconhecido"


@router.get("/usuarios/", response_model=list[UsuarioPublico])
def obter_todos_os_perfil(
    limite: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    busca: str | None = Query(None, max_length=100),
    usuario_logado: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"busca_usuarios:{usuario_logado}", limite=30)
    return usuario_service.buscar_tudo(limite, offset, busca)

@router.get("/usuarios/all", response_model=list[UsuarioDesktop])
def obter_todos_os_perfil(
    usuario_logado: int = Depends(get_usuario_logado),
):
    return usuario_service.buscar_tudo()


@router.get("/usuarios/me", response_model=UsuarioMe)
def obter_perfil_atual(usuario_id: int = Depends(get_usuario_logado)):
    return usuario_service.buscar_por_id(usuario_id)


@router.get("/usuarios/{id_usuario}", response_model=UsuarioPublico)
def buscar_usuario(id_usuario: int, usuario_logado: int = Depends(get_usuario_logado)):
    return usuario_service.buscar_por_id_publico(id_usuario, usuario_logado)


@router.post("/usuarios", response_model=UsuarioCriado, status_code=201)
def criar_usuario(dados: UsuarioInput, request: Request):
    verificar_rate_limit(f"cadastro:{normalizar_email(dados.email)}", limite=5)
    verificar_rate_limit(f"cadastro_ip:{_ip(request)}", limite=20, janela=3600)
    return usuario_service.criar(dados.nome, dados.email, dados.senha)


@router.post("/usuarios/verificar-email", response_model=LoginResponse)
def verificar_email(dados: VerificarEmailInput, request: Request):
    email = normalizar_email(dados.email)
    verificar_rate_limit(f"verificar_email:{email}", limite=10)
    verificar_rate_limit(f"verificar_email_h:{email}", limite=30, janela=3600)
    verificar_rate_limit(f"verificar_email_ip:{_ip(request)}", limite=30)
    return email_verification_service.verificar_codigo(email, dados.codigo, dados.senha)


@router.post("/usuarios/reenviar-codigo", response_model=MensagemResponse)
def reenviar_codigo(dados: ReenviarCodigoInput, request: Request):
    email = normalizar_email(dados.email)
    # 1 por minuto e 5 por hora por email: cada reenvio zera as tentativas
    # do código, então este limite é o que segura a força bruta dos 6 dígitos
    # (e o envio em massa de emails para a caixa de alguém).
    verificar_rate_limit(f"reenviar_codigo:{email}", limite=1)
    verificar_rate_limit(f"reenviar_codigo_h:{email}", limite=5, janela=3600)
    verificar_rate_limit(f"reenviar_codigo_ip:{_ip(request)}", limite=10, janela=3600)
    try:
        email_verification_service.reenviar_codigo(email)
    except EmailDeliveryError as err:
        raise HTTPException(
            status_code=503,
            detail="Nao foi possivel enviar o codigo. Tente novamente mais tarde.",
        ) from err
    return {"mensagem": "Se a conta estiver pendente, um novo codigo sera enviado."}


@router.post("/usuarios/{id_usuario}/confirmar-email", response_model=MensagemResponse)
def confirmar_troca_email(
    id_usuario: int,
    dados: ConfirmarEmailInput,
    usuario_logado: int = Depends(get_usuario_logado),
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    verificar_rate_limit(f"confirmar_email:{usuario_logado}", limite=10)
    return email_verification_service.confirmar_troca_email(id_usuario, dados.codigo)


@router.patch("/usuarios/{id_usuario}/foto", response_model=FotoPerfilResponse)
async def atualizar_foto_usuario(
    id_usuario: int,
    foto: UploadFile = File(...),
    usuario_logado: int = Depends(get_usuario_logado),
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    verificar_rate_limit(f"foto_perfil:{usuario_logado}", limite=10)
    conteudo = await foto.read(_MAX_FOTO_BYTES + 1)
    print(f"[FOTO_PERFIL] filename={foto.filename!r} content_type={foto.content_type!r} size={len(conteudo)}")
    if len(conteudo) > _MAX_FOTO_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Máximo 5 MB.")
    return usuario_service.atualizar_foto(id_usuario, foto.filename or "perfil.jpg", conteudo)


@router.put("/usuarios/{id_usuario}", response_model=UsuarioAtualizadoResponse)
def atualizar_usuario(
    id_usuario: int,
    dados: UsuarioUpdate,
    usuario_logado: int = Depends(get_usuario_logado),
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return usuario_service.atualizar(id_usuario, dados.nome, dados.email, dados.bio)


@router.put("/usuarios/{id_usuario}/senha", response_model=MensagemResponse)
def trocar_senha(
    id_usuario: int,
    dados: TrocarSenhaInput,
    response: Response,
    usuario_logado: int = Depends(get_usuario_logado),
    access_token: str | None = Cookie(default=None),
    refresh_token: str | None = Cookie(default=None),
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    verificar_rate_limit(f"trocar_senha:{usuario_logado}", limite=5)

    resultado = usuario_service.trocar_senha(id_usuario, dados.senha_atual, dados.nova_senha)

    # Revoga a sessão atual e emite tokens novos — mesma sessão continua
    # válida (o usuário não precisa logar de novo), mas qualquer access
    # token antigo copiado/vazado deixa de funcionar imediatamente.
    if access_token:
        revogar_token(access_token)
    if refresh_token:
        revogar_refresh_token(refresh_token)
    _set_auth_cookies(response, id_usuario)

    return resultado


@router.delete("/usuarios/{id_usuario}", response_model=MensagemResponse)
def deletar_usuario(
    id_usuario: int, usuario_logado: int = Depends(get_usuario_logado)
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    return usuario_service.deletar(id_usuario)


@router.post("/usuarios/{id_usuario}/seguir", response_model=SeguirResponse)
def seguir_usuario(
    id_usuario: int,
    usuario_logado: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"seguir:{usuario_logado}", limite=30)
    return usuario_service.seguir(id_usuario, usuario_logado)


@router.get("/usuarios/{id_usuario}/seguidores", response_model=list[UsuarioSimples])
def listar_seguidores(
    id_usuario: int,
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: int = Depends(get_usuario_logado),
):
    return usuario_service.listar_seguidores(id_usuario, limite, offset)


@router.get("/usuarios/{id_usuario}/seguindo", response_model=list[UsuarioSimples])
def listar_seguindo(
    id_usuario: int,
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: int = Depends(get_usuario_logado),
):
    return usuario_service.listar_seguindo(id_usuario, limite, offset)
