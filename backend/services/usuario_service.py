from mysql.connector import Error
from fastapi import HTTPException
from database import get_db
from utils.security import gerar_hash, verificar_senha
from utils.cloudinary_upload import upload_imagem
from utils.imagem_utils import validar_imagem, strip_exif
from utils.rate_limiter import verificar_rate_limit
from services.email_verification_service import (
    EmailDeliveryError,
    enviar_codigo_verificacao,
    gerar_codigo_verificacao,
    normalizar_email,
    solicitar_troca_email,
)


def _enviar_ou_503(email: str, codigo: str, troca_email: bool = False) -> None:
    try:
        enviar_codigo_verificacao(email, codigo, troca_email=troca_email)
    except EmailDeliveryError as err:
        raise HTTPException(
            status_code=503,
            detail="Nao foi possivel enviar o codigo. Tente novamente mais tarde.",
        ) from err

def buscar_tudo(
    busca: str | None = None
) -> list:

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)

        try:
            sql = """
                SELECT
                    id_usuario,
                    nome,
                    bio,
                    email,
                    foto_perfil,
                    data_criacao
                FROM usuarios
            """

            params: list = []

            if busca:
                busca_safe = busca.strip()
                sql += " WHERE nome LIKE %s"
                params.append(f"%{busca_safe}%")          

            cursor.execute(sql, tuple(params))

            return cursor.fetchall()

        finally:
            cursor.close()

def buscar_por_id(usuario_id: int) -> dict:
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
    email = normalizar_email(email)
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            senha_hash = gerar_hash(senha)
            codigo, codigo_hash, expira = gerar_codigo_verificacao()
            cursor.execute(
                "SELECT id_usuario, email_verificado FROM usuarios WHERE email=%s FOR UPDATE",
                (email,),
            )
            existente = cursor.fetchone()
            if existente and existente["email_verificado"]:
                raise HTTPException(status_code=409, detail="Email já cadastrado")
            if existente:
                # Cadastro pendente (nunca verificado): quem se cadastra de novo
                # assume a conta, com novo código. Sem isso, qualquer pessoa
                # poderia "travar" o email de outra cadastrando-o primeiro.
                cursor.execute(
                    """UPDATE usuarios SET nome=%s, senha_hash=%s,
                              codigo_verificacao_hash=%s, codigo_verificacao_expira=%s,
                              tentativas_verificacao=0
                       WHERE id_usuario=%s""",
                    (nome, senha_hash, codigo_hash, expira, existente["id_usuario"]),
                )
                usuario_id = existente["id_usuario"]
            else:
                cursor.execute(
                    """INSERT INTO usuarios
                           (nome, email, senha_hash, email_verificado,
                            codigo_verificacao_hash, codigo_verificacao_expira)
                       VALUES (%s, %s, %s, 0, %s, %s)""",
                    (nome, email, senha_hash, codigo_hash, expira),
                )
                usuario_id = cursor.lastrowid
        except (Error, Exception) as err:
            if hasattr(err, 'errno') and err.errno == 1062:
                raise HTTPException(status_code=409, detail="Email já cadastrado")
            raise
        finally:
            cursor.close()

    # Envia depois do commit para o SMTP não segurar conexão/lock do banco.
    # Se falhar, a conta fica pendente e um novo cadastro a reaproveita.
    _enviar_ou_503(email, codigo)
    return {"mensagem": "Usuário criado com sucesso", "id": usuario_id, "email": email}


def atualizar(usuario_id: int, nome: str, email: str, bio: str | None = None) -> dict:
    """Atualiza nome/bio na hora. Se o email mudou, ele NÃO é trocado aqui:
    fica pendente até o usuário confirmar o código enviado ao novo endereço
    (POST /usuarios/{id}/confirmar-email)."""
    email = normalizar_email(email)
    codigo = None
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT email FROM usuarios WHERE id_usuario=%s FOR UPDATE", (usuario_id,)
            )
            atual = cursor.fetchone()
            if not atual:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            cursor.execute(
                "UPDATE usuarios SET nome=%s, bio=%s WHERE id_usuario=%s",
                (nome, bio, usuario_id),
            )
            if normalizar_email(atual["email"] or "") != email:
                verificar_rate_limit(f"troca_email:{usuario_id}", limite=5, janela=3600)
                codigo = solicitar_troca_email(cursor, usuario_id, email)
        finally:
            cursor.close()

    if codigo is None:
        return {"mensagem": "Usuário atualizado", "email_pendente": False}
    _enviar_ou_503(email, codigo, troca_email=True)
    return {
        "mensagem": "Dados atualizados. Confirme o codigo enviado para o novo email.",
        "email_pendente": True,
    }


def trocar_senha(usuario_id: int, senha_atual: str, nova_senha: str) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT senha_hash FROM usuarios WHERE id_usuario=%s", (usuario_id,)
            )
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            if not verificar_senha(senha_atual, usuario["senha_hash"]):
                raise HTTPException(status_code=401, detail="Senha atual incorreta")

            if verificar_senha(nova_senha, usuario["senha_hash"]):
                raise HTTPException(
                    status_code=400, detail="A nova senha deve ser diferente da senha atual"
                )

            novo_hash = gerar_hash(nova_senha)
            cursor.execute(
                "UPDATE usuarios SET senha_hash=%s WHERE id_usuario=%s",
                (novo_hash, usuario_id),
            )
            return {"mensagem": "Senha alterada com sucesso"}
        finally:
            cursor.close()


def atualizar_foto(usuario_id: int, arquivo_nome: str, arquivo_bytes: bytes) -> dict:
    ext = arquivo_nome.rsplit(".", 1)[-1].lower() if "." in arquivo_nome else ""
    if not ext:
        if arquivo_bytes.startswith(b"\xff\xd8"): ext = "jpg"
        elif arquivo_bytes.startswith(b"\x89PNG"): ext = "png"
        elif b"WEBP" in arquivo_bytes[:16]: ext = "webp"
        else: ext = "jpg"
        from utils.logger import get_logger
        get_logger("usuario_service").info("Extensão de perfil inferida: %s", ext)

    validar_imagem(arquivo_bytes, ext)
    arquivo_bytes = strip_exif(arquivo_bytes, ext)

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
