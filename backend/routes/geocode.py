from fastapi import APIRouter, Depends, HTTPException, Query
from utils.auth import get_usuario_logado
from utils.rate_limiter import verificar_rate_limit
from utils.geoapify_client import autocomplete

router = APIRouter(tags=["Geocodificação"])


@router.get("/geocode/autocomplete")
def autocomplete_cidade(
    text: str = Query(..., min_length=1, max_length=150),
    usuario_id: int = Depends(get_usuario_logado),
):
    """Proxy do autocomplete de cidade do Geoapify — a API key fica só no
    backend, nunca é exposta ao frontend (usado em form-viagem.html e
    chat-viagem.html)."""
    verificar_rate_limit(f"geocode_autocomplete:{usuario_id}", limite=30)
    try:
        features = autocomplete(text)
    except Exception:
        raise HTTPException(
            status_code=502, detail="Serviço de busca de cidade indisponível. Tente novamente."
        )
    return {"features": features}
