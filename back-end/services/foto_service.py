import logging

from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo
from utils.cloudinary_upload import upload_imagem, deletar_imagem
from utils.imagem_utils import validar_imagem, strip_exif, extrair_extensao

logger = logging.getLogger("diartrip.foto")


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
    ext = extrair_extensao(arquivo_nome)
    validar_imagem(arquivo_bytes, ext)
    arquivo_bytes = strip_exif(arquivo_bytes, ext)

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)

            url = upload_imagem(arquivo_bytes, f"diartrip/fotos/{id_grupo}")

            try:
                cursor.execute(
                    "INSERT INTO fotos (id_grupo, id_usuario, caminho_arquivo, template_usado) "
                    "VALUES (%s, %s, %s, %s)",
                    (id_grupo, usuario_id, url, template_usado),
                )
                conexao.commit()
            except Exception:
                try:
                    deletar_imagem(url)
                except Exception as cleanup_exc:
                    logger.error(
                        "Imagem órfã no Cloudinary após falha de DB — url=%s: %s",
                        url, cleanup_exc,
                    )
                raise

            return {"mensagem": "Upload realizado", "url": url, "id_grupo": id_grupo}
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

            deletar_imagem(foto["caminho_arquivo"])

            return {"mensagem": "Foto removida"}
        finally:
            cursor.close()
