"""Cliente Open-Meteo — backup gratuito (sem API key) do OpenWeatherMap.

Usado por utils/apis_externas.py quando o OpenWeather falha, está sem key ou
não cobre os dias pedidos. Vantagem extra: a previsão diária do Open-Meteo
cobre até 16 dias (o plano gratuito do OpenWeather cobre ~5), então viagens
um pouco mais distantes também recebem informação de clima.

O retorno tem exatamente o formato de utils/openweather_client.previsao_por_dia.
"""
import os
import logging
import httpx

logger = logging.getLogger("diartrip.openmeteo")

_URL = os.getenv("OPENMETEO_URL", "https://api.open-meteo.com/v1/forecast")
_TIMEOUT = 8.0

# Códigos WMO usados pelo Open-Meteo → descrição em português
_DESCRICOES_WMO = {
    0: "céu limpo", 1: "predominantemente limpo", 2: "parcialmente nublado", 3: "nublado",
    45: "neblina", 48: "neblina com geada",
    51: "garoa leve", 53: "garoa moderada", 55: "garoa intensa",
    56: "garoa congelante leve", 57: "garoa congelante intensa",
    61: "chuva leve", 63: "chuva moderada", 65: "chuva forte",
    66: "chuva congelante leve", 67: "chuva congelante forte",
    71: "neve leve", 73: "neve moderada", 75: "neve forte", 77: "grãos de neve",
    80: "pancadas de chuva leves", 81: "pancadas de chuva moderadas", 82: "pancadas de chuva fortes",
    85: "pancadas de neve leves", 86: "pancadas de neve fortes",
    95: "trovoadas", 96: "trovoadas com granizo leve", 99: "trovoadas com granizo forte",
}

# Mesma regra do OpenWeather: chuva, garoa, neve e trovoada contam como "chuva"
_CODIGOS_CHUVA = set(range(51, 68)) | set(range(71, 78)) | set(range(80, 87)) | set(range(95, 100))


def previsao_por_dia(lat: float, lon: float) -> dict[str, dict]:
    """Retorna {"YYYY-MM-DD": {"resumo": str, "chuva": bool}} para os próximos
    16 dias. Dict vazio se indisponível — nunca lança."""
    try:
        resp = httpx.get(
            _URL,
            params={
                "latitude": lat, "longitude": lon,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                "timezone": "auto", "forecast_days": 16,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        diario = resp.json().get("daily") or {}
    except Exception as exc:
        logger.warning("Open-Meteo falhou: %s", exc)
        return {}

    dias = diario.get("time") or []
    codigos = diario.get("weather_code") or []
    maximas = diario.get("temperature_2m_max") or []
    minimas = diario.get("temperature_2m_min") or []

    resultado: dict[str, dict] = {}
    for i, dia in enumerate(dias):
        try:
            codigo, t_max, t_min = codigos[i], maximas[i], minimas[i]
        except IndexError:
            continue
        if codigo is None or t_max is None or t_min is None:
            continue
        temp_media = round((t_max + t_min) / 2)
        descricao = _DESCRICOES_WMO.get(int(codigo), "")
        resultado[dia] = {
            "resumo": f"{descricao}, ~{temp_media}°C" if descricao else f"~{temp_media}°C",
            "chuva": int(codigo) in _CODIGOS_CHUVA,
        }
    return resultado
