from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator, Field
from typing import Optional, List
from utils.auth import get_usuario_logado
from services import gasto_service

router = APIRouter(tags=["Gastos"])


class GastoInput(BaseModel):
    valor: float
    categoria: str = Field(..., max_length=50)
    descricao: Optional[str] = Field(None, max_length=255)
    data_gasto: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    id_usuarios_divisao: Optional[List[int]] = []

    @field_validator("valor")
    @classmethod
    def valor_deve_ser_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("O valor deve ser maior que zero")
        return v


class GastoUpdate(BaseModel):
    valor: float
    categoria: str = Field(..., max_length=50)
    descricao: str = Field(..., max_length=255)
    id_usuarios_divisao: list[int] | None = None

    @field_validator("valor")
    @classmethod
    def valor_deve_ser_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("O valor deve ser maior que zero")
        return v


@router.get("/grupos/{id_grupo}/gastos")
def listar_gastos(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return gasto_service.listar(id_grupo, usuario_id)


@router.post("/grupos/{id_grupo}/gastos")
def criar_gasto(id_grupo: int, dados: GastoInput, usuario_id: int = Depends(get_usuario_logado)):
    return gasto_service.criar(id_grupo, usuario_id, dados)


@router.get("/grupos/{id_grupo}/balanco")
def obter_balanco_grupo(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return gasto_service.obter_balanco(id_grupo, usuario_id)


@router.put("/gastos/{id_gasto}")
def atualizar_gasto(id_gasto: int, dados: GastoUpdate, usuario_id: int = Depends(get_usuario_logado)):
    return gasto_service.atualizar(id_gasto, dados, usuario_id)


@router.delete("/gastos/{id_gasto}")
def deletar_gasto(id_gasto: int, usuario_id: int = Depends(get_usuario_logado)):
    return gasto_service.deletar(id_gasto, usuario_id)
