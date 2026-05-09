from fastapi import FastAPI
import os
from routes import usuarios, login, grupos_viagem, roteiros, grupos_membros, gastos
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def home():
    return {"mensagem": "API funcionando"}