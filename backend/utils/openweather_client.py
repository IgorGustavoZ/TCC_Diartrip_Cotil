"""Cliente OpenWeatherMap — previsão real para personalizar o roteiro por IA.

Usa o endpoint gratuito "5 day / 3 hour forecast", que só cobre os próximos
~5 dias a partir de agora (não é possível prever o tempo de uma viagem daqui
a alguns meses). Por isso o retorno é sempre um dict — pode vir vazio (viagem
fora da janela de previsão, key não configurada, ou API indisponível) e quem
chama deve continuar gerando o roteiro normalmente sem essa informação.
"""
import os
import logging
from collections import defaultdict

import httpx

logger = logging.getLogger("diartrip.openweather")

_API_KEY = os.getenv("OPENWEATHER_API_KEY")
_TIMEOUT = 8.0

_CONDICOES_CHUVA = {"Rain", "Thunderstorm", "Drizzle", "Snow"}


def previsao_por_dia(lat: float, lon: float) -> dict[str, dict]:
    """Retorna {"YYYY-MM-DD": {"resumo": str, "chuva": bool}} para os dias
    cobertos pela previsão gratuita (~5 dias a partir de hoje). Dict vazio
    se indisponível — nunca lança."""
    if not _API_KEY:
        return {}
    try:
        resp = httpx.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={
                "lat": lat, "lon": lon, "appid": _API_KEY,
                "units": "metric", "lang": "pt_br",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        entradas = resp.json().get("list") or []
    except Exception as exc:
        logger.warning("OpenWeather falhou: %s", exc)
        return {}

    por_dia: dict[str, list[dict]] = defaultdict(list)
    for item in entradas:
        dt_txt = item.get("dt_txt")
        if not dt_txt:
            continue
        dia = dt_txt.split(" ")[0]
        por_dia[dia].append(item)

    resultado: dict[str, dict] = {}
    for dia, itens in por_dia.items():
        temps = [i["main"]["temp"] for i in itens if i.get("main", {}).get("temp") is not None]
        condicoes = [i["weather"][0]["main"] for i in itens if i.get("weather")]
        descricoes = [i["weather"][0]["description"] for i in itens if i.get("weather")]
        if not temps or not condicoes:
            continue
        tem_chuva = any(c in _CONDICOES_CHUVA for c in condicoes)
        temp_media = round(sum(temps) / len(temps))
        descricao = max(set(descricoes), key=descricoes.count) if descricoes else ""
        resultado[dia] = {
            "resumo": f"{descricao}, ~{temp_media}°C" if descricao else f"~{temp_media}°C",
            "chuva": tem_chuva,
        }
    return resultado
