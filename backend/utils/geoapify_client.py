"""Cliente Geoapify — geocodificação e pontos de interesse reais.

A key já é usada hoje no frontend (autocomplete de cidade em form-viagem.html
e chat-viagem.html); aqui ela passa a também ser usada pelo backend, via
GEOAPIFY_API_KEY, para buscar dados reais de destino ao gerar um roteiro com
IA. Se a API falhar ou a key não estiver configurada, as funções retornam
None/lista vazia — quem chama decide como degradar (nunca inventamos dados).
"""
import os
import logging
import httpx

logger = logging.getLogger("diartrip.geoapify")

_API_KEY = os.getenv("GEOAPIFY_API_KEY")
_TIMEOUT = 8.0

_CATEGORIAS_PADRAO = "tourism.sights,tourism.attraction,catering.restaurant,entertainment"


def autocomplete(texto: str, lang: str = "pt") -> list[dict]:
    """Passthrough do autocomplete de cidade do Geoapify (usado pelo formulário
    de criação de viagem). A key nunca é exposta ao frontend — a chamada
    sai sempre daqui, do backend. Lança se a API falhar; quem chama decide
    o código de erro HTTP."""
    if not _API_KEY:
        raise RuntimeError("GEOAPIFY_API_KEY não configurada")
    resp = httpx.get(
        "https://api.geoapify.com/v1/geocode/autocomplete",
        params={"text": texto, "lang": lang, "apiKey": _API_KEY},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("features") or []


def geocodificar(destino: str) -> tuple[float, float] | None:
    """Retorna (lat, lon) do destino, ou None se não encontrado/indisponível."""
    if not _API_KEY or not destino:
        return None
    try:
        resp = httpx.get(
            "https://api.geoapify.com/v1/geocode/search",
            params={"text": destino, "limit": 1, "apiKey": _API_KEY},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        features = resp.json().get("features") or []
        if not features:
            return None
        lon, lat = features[0]["geometry"]["coordinates"]
        return (lat, lon)
    except Exception as exc:
        logger.warning("Geoapify geocode falhou: %s", exc)
        return None


def buscar_pontos_interesse(
    lat: float, lon: float, raio_metros: int = 5000, limite: int = 20
) -> list[dict]:
    """Retorna uma lista de POIs reais já filtrados para os campos relevantes.
    Lista vazia se a API falhar ou não retornar nada — nunca inventa dados."""
    if not _API_KEY:
        return []
    try:
        resp = httpx.get(
            "https://api.geoapify.com/v2/places",
            params={
                "categories": _CATEGORIAS_PADRAO,
                "filter": f"circle:{lon},{lat},{raio_metros}",
                "bias": f"proximity:{lon},{lat}",
                "limit": limite,
                "apiKey": _API_KEY,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        features = resp.json().get("features") or []
        return [_filtrar_poi(f) for f in features if f.get("properties", {}).get("name")]
    except Exception as exc:
        logger.warning("Geoapify places falhou: %s", exc)
        return []


def _filtrar_poi(feature: dict) -> dict:
    """Só os campos relevantes — reduz tokens enviados à IA e evita
    vazar dados que não fazem sentido para o roteiro."""
    p = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates", [None, None])
    return {
        "nome": p.get("name"),
        "categoria": (p.get("categories") or [None])[0],
        "endereco": p.get("formatted"),
        "coordenadas": {"lat": coords[1], "lon": coords[0]},
    }
