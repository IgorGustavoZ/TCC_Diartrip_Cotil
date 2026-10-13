from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from schemas import (
    OpcaoCustoResponse, OpcaoCustoCriada, PagamentoRegistradoResponse,
    ResumoFinanceiroViagemResponse, MensagemResponse,
)
from utils.auth import get_usuario_logado
from services import custo_viagem_service

router = APIRouter(tags=["Custos da viagem"])


class OpcaoCustoInput(BaseModel):
    tipo: str = Field(..., pattern="^(voo|hospedagem)$")
    nome: str = Field(..., min_length=1, max_length=255)
    origem: Optional[str] = Field(None, max_length=255)
    destino: Optional[str] = Field(None, max_length=255)
    data_ida: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    data_volta: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    preco: float = Field(..., gt=0)
    moeda: str = Field("BRL", max_length=10)
    link_externo: Optional[str] = Field(None, max_length=1000)
    detalhes: Optional[dict] = None


class MarcarPagoInput(BaseModel):
    valor: Optional[float] = Field(None, gt=0)
    descricao: Optional[str] = Field(None, max_length=500)
    data_gasto: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    id_usuarios_divisao: Optional[list[int]] = None


@router.post("/grupos/{id_grupo}/custos", response_model=OpcaoCustoCriada, status_code=201)
def salvar_opcao_custo(
    id_grupo: int, dados: OpcaoCustoInput, usuario_id: int = Depends(get_usuario_logado)
):
    return custo_viagem_service.salvar(id_grupo, usuario_id, dados)


@router.get("/grupos/{id_grupo}/custos", response_model=list[OpcaoCustoResponse])
def listar_opcoes_custo(
    id_grupo: int,
    tipo: Optional[str] = Query(None, pattern="^(voo|hospedagem)$"),
    status: Optional[str] = Query(None, pattern="^(salva|orcamento|paga|descartada)$"),
    usuario_id: int = Depends(get_usuario_logado),
):
    return custo_viagem_service.listar(id_grupo, usuario_id, tipo, status)


@router.patch("/grupos/{id_grupo}/custos/{id_opcao}/orcamento", response_model=MensagemResponse)
def adicionar_ao_orcamento(
    id_grupo: int, id_opcao: int, usuario_id: int = Depends(get_usuario_logado)
):
    return custo_viagem_service.marcar_orcamento(id_opcao, id_grupo, usuario_id)


@router.patch("/grupos/{id_grupo}/custos/{id_opcao}/descartar", response_model=MensagemResponse)
def descartar_opcao_custo(
    id_grupo: int, id_opcao: int, usuario_id: int = Depends(get_usuario_logado)
):
    return custo_viagem_service.descartar(id_opcao, id_grupo, usuario_id)


@router.post("/grupos/{id_grupo}/custos/{id_opcao}/pagar", response_model=PagamentoRegistradoResponse)
def pagar_opcao_custo(
    id_grupo: int, id_opcao: int, dados: MarcarPagoInput = MarcarPagoInput(),
    usuario_id: int = Depends(get_usuario_logado),
):
    return custo_viagem_service.marcar_pago(id_opcao, id_grupo, usuario_id, dados)


@router.delete("/grupos/{id_grupo}/custos/{id_opcao}", response_model=MensagemResponse)
def excluir_opcao_custo(
    id_grupo: int, id_opcao: int, usuario_id: int = Depends(get_usuario_logado)
):
    return custo_viagem_service.excluir(id_opcao, id_grupo, usuario_id)


@router.get("/grupos/{id_grupo}/custos/resumo-financeiro", response_model=ResumoFinanceiroViagemResponse)
def resumo_financeiro_viagem(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return custo_viagem_service.resumo_financeiro(id_grupo, usuario_id)
