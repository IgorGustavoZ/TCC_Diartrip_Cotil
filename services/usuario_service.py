from mysql.connector import Error
from fastapi import HTTPException
from database import get_db
from utils.security import gerar_hash
from utils.cloudinary_upload import upload_imagem
from utils.imagem_utils import validar_imagem


def buscar_por_id(usuario_id: int) -> dict:
    """Retorna perfil completo (incluindo email). Usar apenas em /usuarios/me."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_usuario, nome, email, bio, foto_perfil, data_criacao "
                "FROM usuarios WHERE id_usuario=%s",
                (usuario_id,),
            )
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            return usuario
        finally:
            cursor.close()


def buscar_por_id_publico(usuario_id: int) -> dict:
    """Retorna perfil público sem email — usar em endpoints acessíveis por outros usuários."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_usuario, nome, bio, foto_perfil, data_criacao "
                "FROM usuarios WHERE id_usuario=%s",
                (usuario_id,),
            )
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            return usuario
        finally:
            cursor.close()


def criar(nome: str, email: str, senha: str) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            senha_hash = gerar_hash(senha)
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)",
                (nome, email, senha_hash),
            )
            conexao.commit()
            return {"mensagem": "Usuário criado com sucesso", "id": cursor.lastrowid, "email": email}
        except (Error, Exception) as err:
            # Verifica se é erro de duplicidade (MySQL error 1062)
            if hasattr(err, 'errno') and err.errno == 1062:
                raise HTTPException(status_code=409, detail="Email já cadastrado")
            raise
        finally:
            cursor.close()


def atualizar(usuario_id: int, nome: str, email: str, bio: str | None = None) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET nome=%s, email=%s, bio=%s WHERE id_usuario=%s",
                (nome, email, bio, usuario_id),
            )
            conexao.commit()
            return {"mensagem": "Usuário atualizado"}
        except (Error, Exception) as err:
            if hasattr(err, 'errno') and err.errno == 1062:
                raise HTTPException(
                    status_code=409, detail="Este e-mail já está em uso por outro usuário"
                )
            raise
        finally:
            cursor.close()


def atualizar_foto(usuario_id: int, arquivo_nome: str, arquivo_bytes: bytes) -> dict:
    ext = arquivo_nome.rsplit(".", 1)[-1].lower() if "." in arquivo_nome else "jpg"
    validar_imagem(arquivo_bytes, ext)

    # Usa public_id fixo por usuário: o Cloudinary substitui a imagem anterior automaticamente
    foto_url = upload_imagem(arquivo_bytes, "diartrip/perfis", public_id=f"perfil_{usuario_id}")

    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET foto_perfil=%s WHERE id_usuario=%s",
                (foto_url, usuario_id),
            )
            conexao.commit()
            return {"foto_perfil": foto_url}
        finally:
            cursor.close()


def deletar(usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE id_usuario=%s", (usuario_id,))
            conexao.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            return {"mensagem": "Usuário deletado"}
        finally:
            cursor.close()
