import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import get_db

from routes import usuarios, login, grupos_viagem, roteiros, grupos_membros, gastos, chat_ia, fotos, dashboard, posts, chat_grupo

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("diartrip")

app = FastAPI(
    title="Diartrip API",
    version="1.0.0",
    description="API REST para gerenciamento de viagens em grupo.",
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
}


@app.middleware("http")
async def capturar_excecoes(request: Request, call_next):
    try:
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

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/imagens", StaticFiles(directory="imagens"), name="imagens")
app.mount("/lobby-pags", StaticFiles(directory="lobby-pags"), name="lobby-pags")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


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
    try:
        with get_db() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        return {"status": "ok", "banco": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível")
