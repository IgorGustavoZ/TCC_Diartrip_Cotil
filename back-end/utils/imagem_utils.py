import io
import os
import re
from fastapi import HTTPException

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_SIZE = 5 * 1024 * 1024


def extrair_extensao(nome_arquivo: str) -> str:
    """Extrai e normaliza a extensão de forma segura, impedindo path traversal."""
    nome = os.path.basename(nome_arquivo or "")
    nome = re.sub(r"[^\w.\-]", "_", nome)
    partes = nome.rsplit(".", 1)
    return partes[-1].lower() if len(partes) == 2 else ""


def _magic_bytes_ok(conteudo: bytes, ext: str) -> bool:
    if conteudo[:3] == b"\xff\xd8\xff" and ext in {"jpg", "jpeg"}:
        return True
    if conteudo[:4] == b"\x89PNG" and ext == "png":
        return True
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP" and ext == "webp":
        return True
    return False


def strip_exif(conteudo: bytes, ext: str) -> bytes:
    """Re-encodes image without EXIF/GPS metadata. Falls back to original on error."""
    try:
        from PIL import Image  # noqa: PLC0415
        img = Image.open(io.BytesIO(conteudo))
        fmt_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}
        fmt = fmt_map.get(ext.lower(), "JPEG")
        if fmt == "JPEG" and img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        return conteudo


def validar_imagem(conteudo: bytes, ext: str, max_size: int = MAX_SIZE) -> None:
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato não permitido. Use JPG, PNG ou WebP.")
    if len(conteudo) > max_size:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo 5 MB.")
    if not _magic_bytes_ok(conteudo, ext):
        raise HTTPException(status_code=400, detail="O conteúdo do arquivo não corresponde à extensão informada.")
