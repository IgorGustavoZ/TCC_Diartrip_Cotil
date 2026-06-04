from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo


def listar_por_grupo(id_grupo: int, usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                "SELECT id_roteiro, id_grupo, titulo, descricao, data_criacao "
                "FROM roteiros WHERE id_grupo=%s ORDER BY data_criacao ASC",
                (id_grupo,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def listar_por_usuario(usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT r.id_roteiro, r.id_grupo, r.titulo, r.descricao, r.data_criacao
                FROM roteiros r
                JOIN grupo_membros gm ON r.id_grupo = gm.id_grupo
                WHERE gm.id_usuario = %s
                """,
                (usuario_id,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def buscar_por_id(id_roteiro: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_roteiro, id_grupo, titulo, descricao, data_criacao "
                "FROM roteiros WHERE id_roteiro=%s",
                (id_roteiro,),
            )
            roteiro = cursor.fetchone()
            if not roteiro:
                raise HTTPException(status_code=404, detail="Roteiro não encontrado")
            checar_membro_grupo(cursor, roteiro["id_grupo"], usuario_id)
            return roteiro
        finally:
            cursor.close()


def criar(dados, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, dados.id_grupo, usuario_id)
            cursor.execute(
                "INSERT INTO roteiros (id_grupo, titulo, descricao) VALUES (%s, %s, %s)",
                (dados.id_grupo, dados.titulo, dados.descricao),
            )
            conexao.commit()
            return {"mensagem": "Roteiro criado com sucesso", "id": cursor.lastrowid}
        finally:
            cursor.close()


def atualizar(id_roteiro: int, dados, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_grupo FROM roteiros WHERE id_roteiro=%s", (id_roteiro,)
            )
            resultado = cursor.fetchone()
            if not resultado:
                raise HTTPException(status_code=404, detail="Roteiro não encontrado")
            cargo = checar_membro_grupo(cursor, resultado["id_grupo"], usuario_id)
            if cargo != "admin":
                raise HTTPException(status_code=403, detail="Apenas administradores podem editar roteiros")
            cursor.execute(
                "UPDATE roteiros SET titulo=%s, descricao=%s WHERE id_roteiro=%s",
                (dados.titulo, dados.descricao, id_roteiro),
            )
            conexao.commit()
            return {"mensagem": "Roteiro atualizado"}
        finally:
            cursor.close()


def deletar(id_roteiro: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_grupo FROM roteiros WHERE id_roteiro=%s", (id_roteiro,)
            )
            resultado = cursor.fetchone()
            if not resultado:
                raise HTTPException(status_code=404, detail="Roteiro não encontrado")
            cargo = checar_membro_grupo(cursor, resultado["id_grupo"], usuario_id)
            if cargo != "admin":
                raise HTTPException(
                    status_code=403, detail="Apenas administradores podem deletar roteiros"
                )
            cursor.execute("DELETE FROM roteiros WHERE id_roteiro=%s", (id_roteiro,))
            conexao.commit()
            return {"mensagem": "Roteiro deletado com sucesso"}
        finally:
            cursor.close()
