import io
import logging
from fastapi import HTTPException

logger = logging.getLogger("diartrip.imagem")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_SIZE = 5 * 1024 * 1024
MAX_LARGURA = 4096
MAX_ALTURA = 4096
MAX_PIXELS = MAX_LARGURA * MAX_ALTURA  # ~16 MP


def _magic_bytes_ok(conteudo: bytes, ext: str) -> bool:
    if conteudo[:3] == b"\xff\xd8\xff" and ext in {"jpg", "jpeg"}:
        return True
    if conteudo[:4] == b"\x89PNG" and ext == "png":
        return True
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP" and ext == "webp":
        return True
    return False


def strip_exif(conteudo: bytes, ext: str) -> bytes:
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
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Falha ao remover metadados da imagem (ext=%s): %s", ext, exc)
        raise HTTPException(
            status_code=400,
            detail="Não foi possível processar a imagem. Verifique se o arquivo está íntegro e tente novamente.",
        )


def validar_imagem(conteudo: bytes, ext: str, max_size: int = MAX_SIZE) -> None:
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Tentativa de upload com extensão inválida: %r", ext)
        raise HTTPException(status_code=400, detail="Formato não permitido. Use JPG, PNG ou WebP.")
    if len(conteudo) > max_size:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo 5 MB.")
    if not _magic_bytes_ok(conteudo, ext):
        raise HTTPException(
            status_code=400,
            detail="O conteúdo do arquivo não corresponde à extensão informada.",
        )
    _validar_dimensoes(conteudo)


def _validar_dimensoes(conteudo: bytes) -> None:
    import warnings
    try:
        from PIL import Image  # noqa: PLC0415
        Image.MAX_IMAGE_PIXELS = MAX_PIXELS
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(conteudo)) as img:
                w, h = img.size
                if w > MAX_LARGURA or h > MAX_ALTURA:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Imagem muito grande: {w}x{h} px. "
                            f"Máximo permitido: {MAX_LARGURA}x{MAX_ALTURA} px."
                        ),
                    )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Falha ao verificar dimensões da imagem: %s", exc)
        raise HTTPException(
            status_code=400,
            detail="Não foi possível ler a imagem. Verifique se o arquivo está íntegro.",
        )
