"""Companhias aéreas -> código IATA de 2 letras, pro filtro `include_airlines`
da SerpApi (google_flights). Não existe uma base IATA completa no projeto;
esta é uma lista curada das companhias mais relevantes pra quem parte do
Brasil, não o conjunto completo de companhias do mundo — limitação conhecida,
documentada aqui em vez de inventar uma base maior sem necessidade real.
"""

COMPANHIAS_IATA = {
    "LATAM": "LA",
    "GOL": "G3",
    "Azul": "AD",
    "TAP Air Portugal": "TP",
    "Air France": "AF",
    "KLM": "KL",
    "Lufthansa": "LH",
    "British Airways": "BA",
    "Iberia": "IB",
    "American Airlines": "AA",
    "United Airlines": "UA",
    "Delta Air Lines": "DL",
    "Emirates": "EK",
    "Qatar Airways": "QR",
    "Turkish Airlines": "TK",
    "Swiss International Air Lines": "LX",
    "Air Canada": "AC",
    "Copa Airlines": "CM",
    "Avianca": "AV",
    "Aerolíneas Argentinas": "AR",
    "Ethiopia Airlines": "ET",
    "Qantas": "QF",
    "Singapore Airlines": "SQ",
    "Cathay Pacific": "CX",
    "ITA Airways": "AZ",
}


def nomes_para_iata(nomes: list[str]) -> list[str]:
    """Converte nomes de companhias (como aparecem na lista pro usuário) em
    códigos IATA. Nomes não reconhecidos são ignorados — nunca repassados
    como se já fossem um código IATA."""
    codigos = []
    for nome in nomes:
        codigo = COMPANHIAS_IATA.get(nome.strip())
        if codigo:
            codigos.append(codigo)
    return codigos
