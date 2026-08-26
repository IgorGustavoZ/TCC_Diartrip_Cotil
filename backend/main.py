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

from routes import usuarios, login, grupos_viagem, roteiros, grupos_membros, gastos, chat_ia, fotos, dashboard, posts, chat_grupo, explorar_viagens, geocode

load_dotenv()
configurar_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from utils.redis_client import get_redis
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    if get_redis() is None:
        if is_production:
            raise RuntimeError(
                "STARTUP ABORTADO: Redis é obrigatório em produção. "
                "Configure REDIS_URL antes de iniciar a aplicação. "
                "O fallback em memória não é seguro com múltiplos workers "
                "(bypass de rate limit e reutilização de tokens revogados)."
            )
        else:
            logger.warning(
                "Redis indisponível — usando fallback em memória. "
                "Aceitável apenas para desenvolvimento local."
            )
    yield


app = FastAPI(
    title="Diartrip API",
    version="1.0.0",
    description="API REST para gerenciamento de viagens em grupo.",
    lifespan=lifespan,
)

_IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

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
        "img-src 'self' data: https: blob:; "
        "connect-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "form-action 'self'; "
        "frame-ancestors 'self';"
    ),
}

if _IS_PRODUCTION:
    _SECURITY_HEADERS["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

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
        )

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(explorar_viagens.router)
app.include_router(geocode.router)

if os.path.isdir("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
if os.path.isdir("frontend/imagens"):
    app.mount("/imagens", StaticFiles(directory="frontend/imagens"), name="imagens")
if os.path.isdir("frontend/lobby-pags"):
    app.mount("/lobby-pags", StaticFiles(directory="frontend/lobby-pags"), name="lobby-pags")


@app.get("/", tags=["Frontend"])
def index():
    if not os.path.isfile("frontend/index.html"):
        return JSONResponse(status_code=404, content={"detail": "Página não encontrada"})
    return FileResponse("frontend/index.html")


_PAGINAS_PERMITIDAS = {"index", "lobby", "login", "form"}

@app.get("/{page}.html", tags=["Frontend"])
def serve_page(page: str):
    if page not in _PAGINAS_PERMITIDAS:
        return JSONResponse(status_code=404, content={"detail": "Página não encontrada"})
    path = f"frontend/{page}.html"
    if not os.path.isfile(path):
        return JSONResponse(status_code=404, content={"detail": "Página não encontrada"})
    return FileResponse(path)


@app.get("/health", tags=["Health"])
def health():
    db_ok = False
    try:
        with get_db() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        db_ok = True
    except Exception:
        pass

    if not db_ok:
        raise HTTPException(status_code=503, detail={"status": "error"})

    servicos_ok = all([
        bool(os.getenv("OPENROUTER_API_KEY")),
        all(os.getenv(k) for k in (
            "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"
        )),
    ])

    if not servicos_ok:
        return {"status": "degraded"}

    return {"status": "ok"}
