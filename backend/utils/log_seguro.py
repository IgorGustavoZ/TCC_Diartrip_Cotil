"""Descrição de erro segura para log.

Geoapify (apiKey) e OpenWeather (appid) recebem a key na query string, e o
str() de um erro do httpx inclui a URL completa — logar `exc` direto grava a
key em texto puro no log. Use `descrever_erro(exc)` no lugar.
"""
import httpx


def descrever_erro(exc: BaseException) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    if isinstance(exc, httpx.RequestError):
        return type(exc).__name__
    return f"{type(exc).__name__}: {exc}"
