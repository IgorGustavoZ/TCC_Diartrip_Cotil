"""
Proteção CSRF via Double Submit Cookie.

Fluxo:
  1. No login, o servidor emite um cookie `csrf_token` (não-HttpOnly).
  2. O frontend lê esse cookie e envia seu valor no header `X-CSRF-Token`.
  3. O middleware `checar_csrf` valida que cookie e header coincidem.

Por que isso funciona: um atacante de outro domínio não consegue ler o cookie
(Same-Origin Policy) e, portanto, não pode forjar o header correto.
Combinado com SameSite=Strict, o csrf_token nunca sequer é enviado em
requisições cross-site — é defesa em profundidade.
"""
import hmac
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

_METODOS_MUTANTES = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Rotas que não exigem CSRF: o usuário ainda não possui token ao chamar estas.
_CAMINHOS_ISENTOS = frozenset({"/login", "/logout", "/usuarios"})


def gerar_csrf_token() -> str:
    return secrets.token_urlsafe(32)


async def checar_csrf(request: Request) -> JSONResponse | None:
    """Retorna None se OK, ou um JSONResponse 403 se o CSRF falhar."""
    if request.method not in _METODOS_MUTANTES:
        return None
    if request.url.path in _CAMINHOS_ISENTOS:
        return None
    # Requisições sem sessão ativa não têm CSRF token — o handler de rota devolve 401.
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
