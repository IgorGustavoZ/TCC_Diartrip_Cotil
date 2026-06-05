from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo
from utils.rate_limiter import verificar_rate_limit


def listar(id_grupo: int, usuario_id: int, since_id: int = 0) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                """
                SELECT m.id_mensagem, m.conteudo, m.data_envio,
                       u.id_usuario, u.nome, u.foto_perfil
                FROM mensagens_grupo m
                JOIN usuarios u ON m.id_usuario = u.id_usuario
                WHERE m.id_grupo = %s AND m.id_mensagem > %s
                ORDER BY m.data_envio ASC
                LIMIT 100
                """,
                (id_grupo, since_id),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def enviar(id_grupo: int, usuario_id: int, conteudo: str) -> dict:
    verificar_rate_limit(f"chat:{usuario_id}", limite=30)
    if not conteudo.strip():
        raise HTTPException(status_code=400, detail="Mensagem vazia")
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                "INSERT INTO mensagens_grupo (id_grupo, id_usuario, conteudo) VALUES (%s, %s, %s)",
                (id_grupo, usuario_id, conteudo.strip()),
            )
            conexao.commit()
            return {"mensagem": "Enviado", "id_mensagem": cursor.lastrowid}
        finally:
            cursor.close()
