from fastapi import HTTPException

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_SIZE = 5 * 1024 * 1024


def _magic_bytes_ok(conteudo: bytes, ext: str) -> bool:
    if conteudo[:3] == b"\xff\xd8\xff" and ext in {"jpg", "jpeg"}:
        return True
    if conteudo[:4] == b"\x89PNG" and ext == "png":
        return True
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP" and ext == "webp":
        return True
    return False


def validar_imagem(conteudo: bytes, ext: str, max_size: int = MAX_SIZE) -> None:
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato não permitido. Use JPG, PNG ou WebP.")
    if len(conteudo) > max_size:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo 5 MB.")
    if not _magic_bytes_ok(conteudo, ext):
        raise HTTPException(status_code=400, detail="O conteúdo do arquivo não corresponde à extensão informada.")
