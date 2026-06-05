import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import get_db
from utils.logger import configurar_logging, get_logger
from utils.csrf import checar_csrf

from routes import usuarios, login, grupos_viagem, roteiros, grupos_membros, gastos, chat_ia, fotos, dashboard, posts, chat_grupo

load_dotenv()
configurar_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from utils.redis_client import get_redis
    if get_redis() is None and os.getenv("ENVIRONMENT", "development") == "production":
        logger.warning(
            "AVISO DE SEGURANÇA: Redis indisponível em ambiente de produção. "
            "Rate limit e blacklist de tokens operam em memória local — "
            "com múltiplos workers isso permite bypass parcial. Configure REDIS_URL."
        )
    yield


app = FastAPI(
    title="Diartrip API",
    version="1.0.0",
    description="API REST para gerenciamento de viagens em grupo.",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.geoapify.com https://nominatim.openstreetmap.org; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "form-action 'self'; "
        "frame-ancestors 'self';"
        # 'unsafe-inline' é necessário pelo frontend HTML puro com scripts inline.
        # Em produção com frontend separado (React/Vue), remover e usar nonce/hash.
    ),
}


@app.middleware("http")
async def capturar_excecoes(request: Request, call_next):
    try:
        csrf_erro = await checar_csrf(request)
        if csrf_erro is not None:
            for h, v in _SECURITY_HEADERS.items():
                csrf_erro.headers[h] = v
            return csrf_erro
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
    except Exception as exc:
        logger.exception(
            "Erro não tratado: %s %s → %s",
            request.method,
            request.url.path,
            exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor. Tente novamente mais tarde."},
            headers=_SECURITY_HEADERS,
        )


app.include_router(usuarios.router)
app.include_router(login.router)
app.include_router(grupos_viagem.router)
app.include_router(roteiros.router)
app.include_router(grupos_membros.router)
app.include_router(gastos.router)
app.include_router(chat_ia.router)
app.include_router(fotos.router)
app.include_router(dashboard.router)
app.include_router(posts.router)
app.include_router(chat_grupo.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/imagens", StaticFiles(directory="imagens"), name="imagens")
app.mount("/lobby-pags", StaticFiles(directory="lobby-pags"), name="lobby-pags")


@app.get("/", tags=["Frontend"])
def index():
    return FileResponse("index.html")


_PAGINAS_PERMITIDAS = {"index", "lobby", "login", "form"}

@app.get("/{page}.html", tags=["Frontend"])
def serve_page(page: str):
    if page not in _PAGINAS_PERMITIDAS:
        return JSONResponse(status_code=404, content={"detail": "Página não encontrada"})
    return FileResponse(f"{page}.html")


@app.get("/health", tags=["Health"])
def health():
    status: dict = {}

    try:
        with get_db() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        status["banco"] = "ok"
    except Exception:
        status["banco"] = "erro"

    status["openrouter"] = "ok" if os.getenv("OPENROUTER_API_KEY") else "sem_chave"
    status["cloudinary"] = (
        "ok"
        if all(
            os.getenv(k)
            for k in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
        )
        else "sem_chave"
    )

    degradado = [k for k, v in status.items() if v != "ok"]
    if "banco" in degradado:
        raise HTTPException(status_code=503, detail={"status": "erro", **status})
    if degradado:
        return {"status": "degradado", **status}
    return {"status": "ok", **status}
