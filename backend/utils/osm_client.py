"""Cliente OpenStreetMap — backup gratuito (sem API key) do Geoapify.

Usado por utils/apis_externas.py quando o Geoapify falha, está sem key ou
não encontra nada. Três serviços públicos baseados em dados do OSM:

- Photon (komoot)  → autocomplete de cidade (o Nominatim proíbe uso em
  autocomplete pela política de uso, o Photon foi feito pra isso);
- Nominatim        → geocodificação de destino (texto → lat/lon);
- Overpass API     → pontos de interesse ao redor de uma coordenada.

Os retornos imitam o formato do utils/geoapify_client.py para que quem chama
não precise saber qual provedor respondeu. As políticas de uso desses
serviços exigem um User-Agent identificando a aplicação (OSM_USER_AGENT).
"""
import os
import logging
import httpx

logger = logging.getLogger("diartrip.osm")

_TIMEOUT = 10.0

_PHOTON_URL = os.getenv("PHOTON_URL", "https://photon.komoot.io/api/")
_NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
_OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

# Tags OSM equivalentes às categorias do Geoapify usadas no roteiro
# (tourism.sights, tourism.attraction, catering.restaurant, entertainment).
# A ordem define a prioridade quando há mais resultados que o limite —
# atrações primeiro, restaurantes por último. O terceiro campo é o raio
# máximo daquele filtro: o Overpass público responde 504 em cidades densas
# (ex.: Paris com 5 km), então atrações ficam em até 3 km e restaurantes/
# teatros (milhares de elementos) em até 1 km do centro do destino.
_FILTROS_POI = [
    ("tourism", "attraction|museum|viewpoint|gallery|zoo|theme_park|aquarium", 3000),
    ("historic", "monument|memorial|castle|ruins|archaeological_site|fort", 3000),
    ("amenity", "theatre|arts_centre|restaurant", 1000),
]

# Tipos do Photon que representam uma "cidade" para o autocomplete
_TIPOS_CIDADE = {"city", "town", "village", "hamlet", "locality", "district"}


def _headers() -> dict:
    return {"User-Agent": os.getenv("OSM_USER_AGENT", "DiarTrip-TCC/1.0 (backend)")}


def autocomplete(texto: str, limite: int = 5) -> list[dict]:
    """Autocomplete de cidade via Photon, normalizado para o formato de
    feature do Geoapify (properties.city / formatted / lat / lon), que é o que
    form-viagem.html, chat-viagem.html, viagem.html e o app Flutter leem.
    Lança se a API falhar; quem chama decide o que fazer."""
    resp = httpx.get(
        _PHOTON_URL,
        params={"q": texto, "limit": limite},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    features = resp.json().get("features") or []
    return [_normalizar_feature_photon(f) for f in features if f.get("properties")]


def _normalizar_feature_photon(feature: dict) -> dict:
    p = feature.get("properties", {})
    coords = (feature.get("geometry") or {}).get("coordinates") or [None, None]
    nome = p.get("name")
    cidade = p.get("city") or (nome if p.get("type") in _TIPOS_CIDADE else None)
    partes = [nome, p.get("state"), p.get("country")]
    formatted = ", ".join(dict.fromkeys(x for x in partes if x))
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": coords},
        "properties": {
            "name": nome,
            "city": cidade,
            "state": p.get("state"),
            "country": p.get("country"),
            "country_code": (p.get("countrycode") or "").lower() or None,
            "formatted": formatted or nome,
            "lon": coords[0],
            "lat": coords[1],
            "result_type": p.get("type"),
            "fonte": "osm",
        },
    }


def geocodificar(destino: str) -> tuple[float, float] | None:
    """Retorna (lat, lon) do destino via Nominatim, ou None se não
    encontrado/indisponível — nunca lança."""
    if not destino:
        return None
    try:
        resp = httpx.get(
            _NOMINATIM_URL,
            params={"q": destino, "format": "jsonv2", "limit": 1},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        resultados = resp.json() or []
        if not resultados:
            return None
        return (float(resultados[0]["lat"]), float(resultados[0]["lon"]))
    except Exception as exc:
        logger.warning("Nominatim geocode falhou: %s", exc)
        return None


def buscar_pontos_interesse(
    lat: float, lon: float, raio_metros: int = 5000, limite: int = 20
) -> list[dict]:
    """POIs reais via Overpass API, no mesmo formato do Geoapify
    ({nome, categoria, endereco, coordenadas}). Lista vazia se falhar —
    nunca lança e nunca inventa dados."""
    seletores = "".join(
        f'nwr(around:{int(min(raio_metros, raio_max))},{lat},{lon})'
        f'["{chave}"~"^({valores})$"]["name"];'
        for chave, valores, raio_max in _FILTROS_POI
    )
    # Busca mais que o limite pra poder priorizar atrações sobre restaurantes
    consulta = f"[out:json][timeout:15];({seletores});out center {max(limite * 5, 50)};"
    try:
        resp = httpx.post(
            _OVERPASS_URL,
            data={"data": consulta},
            headers=_headers(),
            timeout=_TIMEOUT + 10,
        )
        resp.raise_for_status()
        elementos = resp.json().get("elements") or []
    except Exception as exc:
        logger.warning("Overpass places falhou: %s", exc)
        return []

    pois = [_filtrar_elemento(e) for e in elementos]
    pois = [p for p in pois if p is not None]
    pois.sort(key=lambda p: p.pop("_prioridade"))
    return pois[:limite]


def _filtrar_elemento(elemento: dict) -> dict | None:
    tags = elemento.get("tags") or {}
    nome = tags.get("name")
    if not nome:
        return None

    categoria, prioridade = None, len(_FILTROS_POI)
    for indice, (chave, valores, _) in enumerate(_FILTROS_POI):
        valor = tags.get(chave)
        if valor and valor in valores.split("|"):
            categoria, prioridade = f"{chave}.{valor}", indice
            break

    centro = elemento.get("center") or {}
    lat = elemento.get("lat", centro.get("lat"))
    lon = elemento.get("lon", centro.get("lon"))

    rua = " ".join(x for x in (tags.get("addr:street"), tags.get("addr:housenumber")) if x)
    endereco = ", ".join(x for x in (rua, tags.get("addr:city")) if x) or None

    return {
        "nome": nome,
        "categoria": categoria,
        "endereco": endereco,
        "coordenadas": {"lat": lat, "lon": lon},
        "_prioridade": prioridade,
    }
