import os
import pathlib
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes import usuarios, login, grupos_viagem, roteiros, grupos_membros, gastos, chat_ia, fotos, dashboard, posts

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

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def capturar_excecoes(request: Request, call_next):
    try:
        return await call_next(request)
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

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/imagens", StaticFiles(directory="imagens"), name="imagens")
app.mount("/lobby-pags", StaticFiles(directory="lobby-pags"), name="lobby-pags")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Frontend"])
def index():
    return FileResponse("index.html")


@app.get("/{page}.html", tags=["Frontend"])
def serve_page(page: str):
    file_path = pathlib.Path(f"{page}.html")
    if file_path.exists():
        return FileResponse(str(file_path))
    return JSONResponse(status_code=404, content={"detail": "Página não encontrada"})


@app.get("/health", tags=["Health"])
def health():
    return {"mensagem": "API funcionando"}
