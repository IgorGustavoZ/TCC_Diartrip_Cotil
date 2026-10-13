import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from utils.auth import get_usuario_logado
from utils.rate_limiter import verificar_rate_limit
from utils.serpapi_client import buscar_voos_serpapi, buscar_hoteis_serpapi

logger = logging.getLogger("diartrip.serpapi")

router = APIRouter(tags=["Serpapi"])


def _validar_data(valor: str, campo: str) -> date:
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Data inválida em {campo}: use AAAA-MM-DD")


@router.get("/serpapi/voos")
def buscar_voos(
    origem: str = Query(..., min_length=3, max_length=3),
    destino: str = Query(..., min_length=3, max_length=3),
    data_ida: str = Query(...),
    data_volta: str | None = Query(None),
    adultos: int = Query(1, ge=1, le=9),
    criancas: int = Query(0, ge=0, le=8),
    classe: str | None = Query(None, pattern="^(economy|premium_economy|business|first)$"),
    companhias: list[str] | None = Query(None),
    preco_max: float | None = Query(None, gt=0),
    max_escalas: int | None = Query(None, ge=0, le=2),
    ordenar_por: str | None = Query(None, pattern="^(preco|duracao)$"),
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"serpapi_voos:{usuario_id}", limite=10)

    d_ida = _validar_data(data_ida, "data_ida")
    if data_volta:
        d_volta = _validar_data(data_volta, "data_volta")
        if d_volta < d_ida:
            raise HTTPException(status_code=400, detail="A data de volta não pode ser anterior à data de ida")

    try:
        return buscar_voos_serpapi(
            origem=origem.upper(),
            destino=destino.upper(),
            data_ida=data_ida,
            data_volta=data_volta,
            adultos=adultos,
            criancas=criancas,
            classe=classe,
            companhias=companhias,
            preco_max=preco_max,
            max_escalas=max_escalas,
            ordenar_por=ordenar_por,
        )
    except HTTPException:
        raise
    except Exception as erro:
        logger.error("Erro ao consultar voos na SerpApi: %s", erro, extra={"user_id": usuario_id})
        raise HTTPException(status_code=502, detail="Não foi possível consultar voos agora. Tente novamente mais tarde.")


@router.get("/serpapi/hoteis")
def buscar_hoteis(
    destino: str = Query(..., min_length=2, max_length=150),
    data_entrada: str = Query(...),
    data_saida: str = Query(...),
    adultos: int = Query(2, ge=1, le=9),
    criancas: int = Query(0, ge=0, le=8),
    preco_min: float | None = Query(None, gt=0),
    preco_max: float | None = Query(None, gt=0),
    avaliacao_min: float | None = Query(None, ge=0, le=5),
    estrelas: list[int] | None = Query(None),
    ordenar_por: str | None = Query(None, pattern="^(preco|avaliacao)$"),
    usuario_id: int = Depends(get_usuario_logado),
):
    verificar_rate_limit(f"serpapi_hoteis:{usuario_id}", limite=10)

    d_entrada = _validar_data(data_entrada, "data_entrada")
    d_saida = _validar_data(data_saida, "data_saida")
    if d_saida <= d_entrada:
        raise HTTPException(status_code=400, detail="A data de saída deve ser posterior à data de entrada")
    if preco_min and preco_max and preco_min > preco_max:
        raise HTTPException(status_code=400, detail="preco_min não pode ser maior que preco_max")

    try:
        return buscar_hoteis_serpapi(
            destino=destino,
            data_entrada=data_entrada,
            data_saida=data_saida,
            adultos=adultos,
            criancas=criancas,
            preco_min=preco_min,
            preco_max=preco_max,
            avaliacao_min=avaliacao_min,
            estrelas=estrelas,
            ordenar_por=ordenar_por,
        )
    except HTTPException:
        raise
    except Exception as erro:
        logger.error("Erro ao consultar hotéis na SerpApi: %s", erro, extra={"user_id": usuario_id})
        raise HTTPException(status_code=502, detail="Não foi possível consultar hospedagens agora. Tente novamente mais tarde.")
