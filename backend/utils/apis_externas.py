"""Ponto único de acesso às APIs externas de geo/clima, com backup automático.

Cada função tem a MESMA assinatura e o MESMO formato de retorno da versão
original (utils/geoapify_client.py e utils/openweather_client.py), então
trocar o import é suficiente. A ordem é sempre:

    1. provedor principal (Geoapify / OpenWeather — exigem API key);
    2. se ele falhar, estiver sem key ou não retornar nada, provedor
       secundário gratuito e sem key (OpenStreetMap / Open-Meteo).

Variáveis de ambiente (lidas a cada chamada, para poderem ser trocadas em
teste sem reiniciar):

    APIS_BACKUP_HABILITADO=true   → false desliga os provedores secundários
                                    (comportamento idêntico ao original).
    APIS_FORCAR_BACKUP=false      → true pula o provedor principal e usa SÓ o
                                    secundário. Serve para testar o backup de
                                    ponta a ponta sem precisar derrubar o
                                    principal ou apagar a key.
"""
import os
import logging

from utils.log_seguro import descrever_erro
from utils import geoapify_client, openweather_client, osm_client, openmeteo_client

logger = logging.getLogger("diartrip.apis_externas")


def _flag(nome: str, padrao: str) -> bool:
    return os.getenv(nome, padrao).strip().lower() in ("1", "true", "yes", "sim", "on")


def backup_habilitado() -> bool:
    return _flag("APIS_BACKUP_HABILITADO", "true") or forcar_backup()


def forcar_backup() -> bool:
    return _flag("APIS_FORCAR_BACKUP", "false")


def autocomplete(texto: str, lang: str = "pt") -> list[dict]:
    """Autocomplete de cidade. Lança só se principal E backup falharem
    (a rota GET /geocode/autocomplete transforma isso em 502)."""
    erro_principal: Exception | None = None
    if not forcar_backup():
        try:
            features = geoapify_client.autocomplete(texto, lang=lang)
            if features or not backup_habilitado():
                return features
        except Exception as exc:
            if not backup_habilitado():
                raise
            erro_principal = exc
            logger.warning("Autocomplete principal (Geoapify) falhou, usando backup OSM: %s", descrever_erro(exc))

    try:
        return osm_client.autocomplete(texto)
    except Exception as exc:
        logger.warning("Autocomplete backup (Photon/OSM) falhou: %s", descrever_erro(exc))
        raise erro_principal or exc


def geocodificar(destino: str) -> tuple[float, float] | None:
    """(lat, lon) do destino, ou None se nenhum provedor encontrar."""
    if not forcar_backup():
        coordenadas = geoapify_client.geocodificar(destino)
        if coordenadas or not backup_habilitado():
            return coordenadas
        logger.info("Geocode principal sem resultado, tentando backup OSM")
    return osm_client.geocodificar(destino)


def buscar_pontos_interesse(
    lat: float, lon: float, raio_metros: int = 5000, limite: int = 20
) -> list[dict]:
    """POIs reais ao redor da coordenada; lista vazia se nenhum provedor
    retornar nada — nunca inventa dados."""
    if not forcar_backup():
        pois = geoapify_client.buscar_pontos_interesse(lat, lon, raio_metros=raio_metros, limite=limite)
        if pois or not backup_habilitado():
            return pois
        logger.info("POIs principal sem resultado, tentando backup Overpass/OSM")
    return osm_client.buscar_pontos_interesse(lat, lon, raio_metros=raio_metros, limite=limite)


def previsao_por_dia(lat: float, lon: float) -> dict[str, dict]:
    """Previsão diária {"YYYY-MM-DD": {"resumo", "chuva"}}; dict vazio se
    nenhum provedor tiver dados — nunca lança."""
    if not forcar_backup():
        previsao = openweather_client.previsao_por_dia(lat, lon)
        if previsao or not backup_habilitado():
            return previsao
        logger.info("Previsão principal vazia, tentando backup Open-Meteo")
    return openmeteo_client.previsao_por_dia(lat, lon)
