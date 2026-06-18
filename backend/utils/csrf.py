import hmac
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

_METODOS_MUTANTES = frozenset({"POST", "PUT", "PATCH", "DELETE"})

_CAMINHOS_ISENTOS = frozenset({"/login", "/token/refresh"})


def gerar_csrf_token() -> str:
    return secrets.token_urlsafe(32)


async def checar_csrf(request: Request) -> JSONResponse | None:
    if request.method not in _METODOS_MUTANTES:
        return None
    if request.url.path in _CAMINHOS_ISENTOS:
        return None
    if not request.cookies.get("access_token"):
        return None

    cookie = request.cookies.get("csrf_token", "")
    header = request.headers.get("x-csrf-token", "")

    if not cookie or not header:
        return JSONResponse(
            status_code=403,
            content={"detail": "Token CSRF ausente. Faça login novamente."},
        )
    if not hmac.compare_digest(cookie, header):
        return JSONResponse(
            status_code=403,
            content={"detail": "Token CSRF inválido."},
        )
    return None
