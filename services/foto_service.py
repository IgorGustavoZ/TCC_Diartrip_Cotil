import os
import uuid
from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_SIZE = 5 * 1024 * 1024


def _validar_magic_bytes(conteudo: bytes, ext: str) -> bool:
    if conteudo[:3] == b"\xff\xd8\xff" and ext in {"jpg", "jpeg"}:
        return True
    if conteudo[:4] == b"\x89PNG" and ext == "png":
        return True
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP" and ext == "webp":
        return True
    return False


def listar(id_grupo: int, usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                """
                SELECT f.id_foto, f.caminho_arquivo, f.template_usado, f.data_upload, u.nome
                FROM fotos f
                JOIN usuarios u ON f.id_usuario = u.id_usuario
                WHERE f.id_grupo = %s
                ORDER BY f.data_upload DESC
                """,
                (id_grupo,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def salvar(
    id_grupo: int,
    usuario_id: int,
    arquivo_nome: str,
    arquivo_bytes: bytes,
    arquivo_size: int,
    template_usado: str | None,
) -> dict:
    ext = arquivo_nome.split(".")[-1].lower() if arquivo_nome else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato não permitido. Use JPG, PNG ou WebP.")
    if arquivo_size > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo 5 MB.")
    if not _validar_magic_bytes(arquivo_bytes, ext):
        raise HTTPException(
            status_code=400,
            detail="O conteúdo do arquivo não corresponde à extensão informada.",
        )

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            # Verifica pertencimento ANTES de gravar qualquer arquivo em disco
            checar_membro_grupo(cursor, id_grupo, usuario_id)

            nome_arquivo = f"{uuid.uuid4()}.{ext}"
            caminho = os.path.join(UPLOAD_DIR, nome_arquivo)
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            with open(caminho, "wb") as f:
                f.write(arquivo_bytes)

            caminho_db = f"/uploads/{nome_arquivo}"
            try:
                cursor.execute(
                    "INSERT INTO fotos (id_grupo, id_usuario, caminho_arquivo, template_usado) "
                    "VALUES (%s, %s, %s, %s)",
                    (id_grupo, usuario_id, caminho_db, template_usado),
                )
                conexao.commit()
            except Exception:
                # Remove o arquivo físico se o INSERT falhar
                try:
                    os.remove(caminho)
                except OSError:
                    pass
                raise

            return {"mensagem": "Upload realizado", "url": caminho_db, "id_grupo": id_grupo}
        finally:
            cursor.close()


def deletar(id_foto: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_usuario, id_grupo, caminho_arquivo FROM fotos WHERE id_foto=%s",
                (id_foto,),
            )
            foto = cursor.fetchone()
            if not foto:
                raise HTTPException(status_code=404, detail="Foto não encontrada")

            cargo = checar_membro_grupo(cursor, foto["id_grupo"], usuario_id)
            if usuario_id != foto["id_usuario"] and cargo != "admin":
                raise HTTPException(status_code=403, detail="Sem permissão")

            cursor.execute("DELETE FROM fotos WHERE id_foto=%s", (id_foto,))
            conexao.commit()

            caminho_fisico = os.path.join(UPLOAD_DIR, os.path.basename(foto["caminho_arquivo"]))
            try:
                if os.path.exists(caminho_fisico):
                    os.remove(caminho_fisico)
            except OSError as e:
                print(f"Falha ao remover arquivo {caminho_fisico}: {e}")

            return {"mensagem": "Foto removida"}
        finally:
            cursor.close()
