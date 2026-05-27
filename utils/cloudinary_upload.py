import io
import logging
import os
import threading

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException

logger = logging.getLogger("diartrip.cloudinary")

_configurado = False
_config_lock = threading.Lock()


def _configurar() -> None:
    global _configurado
    if not _configurado:
        with _config_lock:
            if not _configurado:
                cloudinary.config(
                    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
                    api_key=os.getenv("CLOUDINARY_API_KEY"),
                    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
                    secure=True,
                )
                _configurado = True


def upload_imagem(conteudo: bytes, pasta: str, public_id: str | None = None) -> str:
    _configurar()
    kwargs: dict = {"folder": pasta, "resource_type": "image"}
    if public_id:
        kwargs["public_id"] = public_id
        kwargs["overwrite"] = True
        kwargs["invalidate"] = True
    try:
        resultado = cloudinary.uploader.upload(io.BytesIO(conteudo), **kwargs)
        return resultado["secure_url"]
    except Exception as exc:
        logger.error("Cloudinary upload falhou — pasta=%s: %s", pasta, exc)
        raise HTTPException(
            status_code=502,
            detail="Serviço de armazenamento de imagens indisponível. Tente novamente.",
        )


def deletar_imagem(url: str) -> None:
    if not url or "cloudinary.com" not in url:
        return
    _configurar()
    try:
        # URL: https://res.cloudinary.com/cloud/image/upload/vXXX/pasta/arquivo.ext
        partes = url.split("/upload/")
        if len(partes) < 2:
            return
        caminho = partes[1]
        if caminho.startswith("v") and "/" in caminho:
            caminho = caminho.split("/", 1)[1]
        public_id = caminho.rsplit(".", 1)[0]
        cloudinary.uploader.destroy(public_id)
    except Exception as exc:
        logger.warning("Falha ao deletar imagem no Cloudinary (url=%s): %s", url, exc)
