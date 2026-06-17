from mysql.connector import Error
from fastapi import HTTPException
from database import get_db
from utils.security import gerar_hash
from utils.cloudinary_upload import upload_imagem
from utils.imagem_utils import validar_imagem, strip_exif

def buscar_tudo(limite: int = 20, offset: int = 0, busca: str | None = None) -> list:
    """Retorna perfis públicos com paginação obrigatória — nunca inclui senha_hash ou email."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            sql = "SELECT id_usuario, nome, bio, foto_perfil FROM usuarios"
            params: list = []
            if busca:
                busca_safe = busca.strip()
                sql += " WHERE nome LIKE %s"
                params.append(f"%{busca_safe}%")
            sql += " ORDER BY id_usuario LIMIT %s OFFSET %s"
            params.extend([limite, offset])
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

def buscar_por_id(usuario_id: int) -> dict:
    """Retorna perfil completo (incluindo email). Usar apenas em /usuarios/me."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT u.id_usuario, u.nome, u.email, u.bio, u.foto_perfil, u.data_criacao,
                       (SELECT COUNT(*) FROM seguidores WHERE id_seguido  = u.id_usuario) AS seguidores,
                       (SELECT COUNT(*) FROM seguidores WHERE id_seguidor = u.id_usuario) AS seguindo
                FROM usuarios u WHERE u.id_usuario = %s
                """,
                (usuario_id,),
            )
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            return usuario
        finally:
            cursor.close()


def buscar_por_id_publico(usuario_id: int, viewer_id: int) -> dict:
    """Retorna perfil público sem email — usar em endpoints acessíveis por outros usuários."""
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT u.id_usuario, u.nome, u.bio, u.foto_perfil, u.data_criacao,
                       (SELECT COUNT(*) FROM seguidores WHERE id_seguido  = u.id_usuario) AS seguidores,
                       (SELECT COUNT(*) FROM seguidores WHERE id_seguidor = u.id_usuario) AS seguindo
                FROM usuarios u WHERE u.id_usuario = %s
                """,
                (usuario_id,),
            )
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            cursor.execute(
                "SELECT 1 FROM seguidores WHERE id_seguidor=%s AND id_seguido=%s",
                (viewer_id, usuario_id),
            )
            usuario["ja_segue"] = cursor.fetchone() is not None
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
            return {"mensagem": "Usuário criado com sucesso", "id": cursor.lastrowid, "email": email}
        except (Error, Exception) as err:
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
    # Extrai extensão do nome do arquivo
    ext = arquivo_nome.rsplit(".", 1)[-1].lower() if "." in arquivo_nome else ""
    
    # Se não houver extensão no nome, tenta inferir pelos magic bytes
    if not ext:
        if arquivo_bytes.startswith(b"\xff\xd8"): ext = "jpg"
        elif arquivo_bytes.startswith(b"\x89PNG"): ext = "png"
        elif b"WEBP" in arquivo_bytes[:16]: ext = "webp"
        else: ext = "jpg" # Fallback final
        from utils.logger import get_logger
        get_logger("usuario_service").info("Extensão de perfil inferida: %s", ext)

    validar_imagem(arquivo_bytes, ext)
    arquivo_bytes = strip_exif(arquivo_bytes, ext)

    # Usa public_id fixo por usuário: o Cloudinary substitui a imagem anterior automaticamente
    foto_url = upload_imagem(arquivo_bytes, "diartrip/perfis", public_id=f"perfil_{usuario_id}")

    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET foto_perfil=%s WHERE id_usuario=%s",
                (foto_url, usuario_id),
            )
            return {"foto_perfil": foto_url}
        finally:
            cursor.close()


def seguir(id_seguido: int, id_seguidor: int) -> dict:
    if id_seguido == id_seguidor:
        raise HTTPException(status_code=400, detail="Você não pode seguir a si mesmo")
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute("SELECT 1 FROM usuarios WHERE id_usuario=%s", (id_seguido,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            cursor.execute(
                "SELECT 1 FROM seguidores WHERE id_seguidor=%s AND id_seguido=%s",
                (id_seguidor, id_seguido),
            )
            if cursor.fetchone():
                cursor.execute(
                    "DELETE FROM seguidores WHERE id_seguidor=%s AND id_seguido=%s",
                    (id_seguidor, id_seguido),
                )
                seguindo = False
            else:
                cursor.execute(
                    "INSERT INTO seguidores (id_seguidor, id_seguido) VALUES (%s, %s)",
                    (id_seguidor, id_seguido),
                )
                seguindo = True

            cursor.execute(
                "SELECT COUNT(*) AS total FROM seguidores WHERE id_seguido=%s",
                (id_seguido,),
            )
            total = cursor.fetchone()["total"]
            return {"seguindo": seguindo, "total_seguidores": total}
        finally:
            cursor.close()


def listar_seguidores(id_usuario: int, limite: int = 50, offset: int = 0) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT u.id_usuario, u.nome, u.foto_perfil
                FROM seguidores s
                JOIN usuarios u ON s.id_seguidor = u.id_usuario
                WHERE s.id_seguido = %s
                ORDER BY s.data_criacao DESC
                LIMIT %s OFFSET %s
                """,
                (id_usuario, limite, offset),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def listar_seguindo(id_usuario: int, limite: int = 50, offset: int = 0) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT u.id_usuario, u.nome, u.foto_perfil
                FROM seguidores s
                JOIN usuarios u ON s.id_seguido = u.id_usuario
                WHERE s.id_seguidor = %s
                ORDER BY s.data_criacao DESC
                LIMIT %s OFFSET %s
                """,
                (id_usuario, limite, offset),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def deletar(usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE id_usuario=%s", (usuario_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            return {"mensagem": "Usuário deletado"}
        finally:
            cursor.close()
