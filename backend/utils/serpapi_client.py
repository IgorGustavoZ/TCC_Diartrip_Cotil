"""Cliente SerpApi (Google Flights / Google Hotels). Só monta parâmetros
oficiais da API e devolve resultados CURADOS (campos específicos pra exibir
na interface) — nunca o dict bruto da SerpApi, que é enorme e carrega muito
mais do que a aplicação precisa.
"""
import os

import serpapi

from utils.iata_airlines import nomes_para_iata

_CLASSES_VIAGEM = {"economy": 1, "premium_economy": 2, "business": 3, "first": 4}


def _cliente() -> "serpapi.Client":
    return serpapi.Client(api_key=os.getenv("SERPAPI_API_KEY"))


def _stops_param(max_escalas: int | None) -> int | None:
    """SerpApi: 1=sem escala, 2=até 1 escala, 3=até 2 escalas. None/omitido = qualquer quantidade."""
    if max_escalas is None:
        return None
    if max_escalas <= 0:
        return 1
    if max_escalas == 1:
        return 2
    return 3


def _rating_param(avaliacao_min: float | None) -> int | None:
    """SerpApi (google_hotels): 7=3.5+, 8=4.0+, 9=4.5+ — confirmado nos testes
    manuais contra a API real (ver análise antes da implementação)."""
    if avaliacao_min is None:
        return None
    if avaliacao_min >= 4.5:
        return 9
    if avaliacao_min >= 4.0:
        return 8
    if avaliacao_min >= 3.5:
        return 7
    return None


def _curar_voo(entry: dict) -> dict:
    pernas = entry.get("flights") or []
    primeira = pernas[0] if pernas else {}
    ultima = pernas[-1] if pernas else {}
    companhias = sorted({p.get("airline") for p in pernas if p.get("airline")})
    return {
        "preco": entry.get("price"),
        "tipo": entry.get("type"),
        "duracao_total_min": entry.get("total_duration"),
        "escalas": len(entry.get("layovers") or []),
        "companhia_principal": primeira.get("airline"),
        "companhia_logo": entry.get("airline_logo") or primeira.get("airline_logo"),
        "companhias": companhias,
        "classe": primeira.get("travel_class"),
        "partida": {
            "aeroporto_id": (primeira.get("departure_airport") or {}).get("id"),
            "aeroporto_nome": (primeira.get("departure_airport") or {}).get("name"),
            "horario": (primeira.get("departure_airport") or {}).get("time"),
        },
        "chegada": {
            "aeroporto_id": (ultima.get("arrival_airport") or {}).get("id"),
            "aeroporto_nome": (ultima.get("arrival_airport") or {}).get("name"),
            "horario": (ultima.get("arrival_airport") or {}).get("time"),
        },
    }


def buscar_voos_serpapi(
    origem: str,
    destino: str,
    data_ida: str,
    data_volta: str | None = None,
    adultos: int = 1,
    criancas: int = 0,
    classe: str | None = None,
    companhias: list[str] | None = None,
    preco_max: float | None = None,
    max_escalas: int | None = None,
    ordenar_por: str | None = None,
) -> dict:
    parametros = {
        "engine": "google_flights",
        "departure_id": origem,
        "arrival_id": destino,
        "outbound_date": data_ida,
        "type": 1 if data_volta else 2,
        "adults": adultos,
        "currency": "BRL",
        "hl": "pt-BR",
        "gl": "br",
    }
    if data_volta:
        parametros["return_date"] = data_volta
    if criancas:
        parametros["children"] = criancas
    if classe and classe in _CLASSES_VIAGEM:
        parametros["travel_class"] = _CLASSES_VIAGEM[classe]
    if companhias:
        codigos = nomes_para_iata(companhias)
        if codigos:
            parametros["include_airlines"] = ",".join(codigos)
    if preco_max:
        parametros["max_price"] = int(preco_max)
    stops = _stops_param(max_escalas)
    if stops is not None:
        parametros["stops"] = stops
    if ordenar_por == "preco":
        parametros["sort_by"] = 2
    elif ordenar_por == "duracao":
        parametros["sort_by"] = 5

    resultados = _cliente().search(parametros).as_dict()
    brutos = (resultados.get("best_flights") or []) + (resultados.get("other_flights") or [])
    return {
        "voos": [_curar_voo(v) for v in brutos],
        "link_busca": (resultados.get("search_metadata") or {}).get("google_flights_url"),
        "preco_mais_baixo": (resultados.get("price_insights") or {}).get("lowest_price"),
    }


def _curar_hotel(entry: dict) -> dict:
    return {
        "nome": entry.get("name"),
        "tipo": entry.get("type"),
        "descricao": entry.get("description"),
        "imagem": ((entry.get("images") or [{}])[0]).get("thumbnail"),
        "avaliacao": entry.get("overall_rating"),
        "num_avaliacoes": entry.get("reviews"),
        "classificacao_estrelas": entry.get("hotel_class"),
        "preco_por_noite": (entry.get("rate_per_night") or {}).get("extracted_lowest"),
        "preco_total": (entry.get("total_rate") or {}).get("extracted_lowest"),
        "comodidades": entry.get("amenities") or [],
        "link": entry.get("link"),
        "propriedade_token": entry.get("property_token"),
    }


def buscar_hoteis_serpapi(
    destino: str,
    data_entrada: str,
    data_saida: str,
    adultos: int = 2,
    criancas: int = 0,
    preco_min: float | None = None,
    preco_max: float | None = None,
    avaliacao_min: float | None = None,
    estrelas: list[int] | None = None,
    ordenar_por: str | None = None,
) -> dict:
    parametros = {
        "engine": "google_hotels",
        "q": destino,
        "check_in_date": data_entrada,
        "check_out_date": data_saida,
        "adults": adultos,
        "currency": "BRL",
        "hl": "pt-BR",
        "gl": "br",
    }
    if criancas:
        parametros["children"] = criancas
    if preco_min:
        parametros["min_price"] = int(preco_min)
    if preco_max:
        parametros["max_price"] = int(preco_max)
    rating = _rating_param(avaliacao_min)
    if rating is not None:
        parametros["rating"] = rating
    if estrelas:
        validas = [str(e) for e in estrelas if e in (2, 3, 4, 5)]
        if validas:
            parametros["hotel_class"] = ",".join(validas)

    resultados = _cliente().search(parametros).as_dict()
    propriedades = resultados.get("properties") or []
    hoteis = [_curar_hotel(h) for h in propriedades]

    # O parâmetro sort_by da SerpApi pra google_hotels não se mostrou
    # confiável em testes manuais (preços não saíam em ordem); ordenar no
    # resultado já curado é garantidamente correto.
    if ordenar_por == "preco":
        hoteis.sort(key=lambda h: h["preco_por_noite"] if h["preco_por_noite"] is not None else float("inf"))
    elif ordenar_por == "avaliacao":
        hoteis.sort(key=lambda h: h["avaliacao"] if h["avaliacao"] is not None else -1, reverse=True)

    return {
        "hoteis": hoteis,
        "link_busca": (resultados.get("search_metadata") or {}).get("google_hotels_url"),
    }
