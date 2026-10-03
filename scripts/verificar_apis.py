"""Verifica AO VIVO cada API externa do backend (principal e backup).

Uso (a partir da raiz do projeto):
    python scripts/verificar_apis.py            # testa tudo
    python scripts/verificar_apis.py --sem-ia   # pula IA (não gasta créditos)

Lê as keys de backend/.env. Não altera nada no banco; só faz requisições de
leitura. Código de saída 1 se algum provedor CONFIGURADO falhar.
"""
import os
import sys
import time

BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
sys.path.insert(0, BACKEND)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(BACKEND, ".env"))

from utils import geoapify_client, openweather_client, osm_client, openmeteo_client  # noqa: E402

DESTINO = "Paris"
LAT, LON = 48.8566, 2.3522

falhas = 0


def checar(nome, func, configurado=True):
    global falhas
    if not configurado:
        print(f"  [--]   {nome}: não configurado (pulado)")
        return
    t0 = time.monotonic()
    try:
        resultado = func()
        ms = int((time.monotonic() - t0) * 1000)
        ok = bool(resultado)
        resumo = repr(resultado)[:90]
        print(f"  [{'OK' if ok else 'VAZIO'}]   {nome} ({ms} ms): {resumo}")
        if not ok:
            falhas += 1
    except Exception as exc:
        falhas += 1
        print(f"  [FALHA] {nome}: {exc}")


print("Geocodificação / autocomplete / POIs")
tem_geoapify = bool(os.getenv("GEOAPIFY_API_KEY"))
checar("Geoapify autocomplete (principal)", lambda: geoapify_client.autocomplete("Par")[:1], tem_geoapify)
checar("Photon autocomplete (backup)", lambda: osm_client.autocomplete("Par")[:1])
checar("Geoapify geocode (principal)", lambda: geoapify_client.geocodificar(DESTINO), tem_geoapify)
checar("Nominatim geocode (backup)", lambda: osm_client.geocodificar(DESTINO))
checar("Geoapify POIs (principal)", lambda: geoapify_client.buscar_pontos_interesse(LAT, LON, limite=3), tem_geoapify)
checar("Overpass POIs (backup)", lambda: osm_client.buscar_pontos_interesse(LAT, LON, raio_metros=1500, limite=3))

print("Clima")
checar("OpenWeather (principal)", lambda: openweather_client.previsao_por_dia(LAT, LON),
       bool(os.getenv("OPENWEATHER_API_KEY")))
checar("Open-Meteo (backup)", lambda: openmeteo_client.previsao_por_dia(LAT, LON))

if "--sem-ia" not in sys.argv:
    from utils import ia_client

    msg = [{"role": "user", "content": "Responda só: ok"}]
    print("IA")
    checar(f"OpenRouter principal ({ia_client.IA_MODEL})",
           lambda: ia_client._principal.chat.completions.create(
               model=ia_client.IA_MODEL, messages=msg, max_tokens=5).choices[0].message.content,
           bool(os.getenv("OPENROUTER_API_KEY")))
    for modelo in ia_client._modelos_backup_openrouter():
        checar(f"OpenRouter backup ({modelo})",
               lambda m=modelo: ia_client._principal.chat.completions.create(
                   model=m, messages=msg, max_tokens=5).choices[0].message.content)
    checar("Provedor IA secundário",
           lambda: ia_client._backup[0].chat.completions.create(
               model=ia_client._backup[1], messages=msg, max_tokens=5).choices[0].message.content,
           ia_client._backup is not None)

print()
print("Tudo OK." if not falhas else f"{falhas} verificação(ões) com problema.")
sys.exit(1 if falhas else 0)
