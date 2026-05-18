import mysql.connector
from fastapi import HTTPException
from database import get_db
from utils.security import gerar_hash


def buscar_por_id(usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_usuario, nome, email, foto_perfil, data_criacao "
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
        except mysql.connector.Error as err:
            if err.errno == 1062:
                raise HTTPException(status_code=409, detail="Email já cadastrado")
            raise
        finally:
            cursor.close()


def atualizar(usuario_id: int, nome: str, email: str) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET nome=%s, email=%s WHERE id_usuario=%s",
                (nome, email, usuario_id),
            )
            conexao.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            return {"mensagem": "Usuário atualizado"}
        except mysql.connector.Error as err:
            if err.errno == 1062:
                raise HTTPException(
                    status_code=409, detail="Este e-mail já está em uso por outro usuário"
                )
            raise
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
