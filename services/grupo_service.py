import os
import random
import string
from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo


def listar_por_usuario(usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT g.id_grupo, g.nome_grupo, g.destino_principal,
                       g.data_inicio, g.data_fim, g.codigo_convite, u.nome AS criador
                FROM grupos_viagem g
                JOIN usuarios u ON g.criado_por = u.id_usuario
                JOIN grupo_membros gm ON gm.id_grupo = g.id_grupo
                WHERE gm.id_usuario = %s
                """,
                (usuario_id,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def buscar_por_nome(usuario_id: int, nome: str | None) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            sql = """
                SELECT g.id_grupo, g.nome_grupo, g.destino_principal,
                       g.data_inicio, g.data_fim, g.codigo_convite, u.nome AS criador
                FROM grupos_viagem g
                JOIN usuarios u ON g.criado_por = u.id_usuario
                JOIN grupo_membros gm ON gm.id_grupo = g.id_grupo
                WHERE gm.id_usuario = %s
            """
            params: list = [usuario_id]
            if nome:
                sql += " AND g.nome_grupo LIKE %s"
                params.append(f"%{nome}%")
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()


def buscar_por_id(id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                """
                SELECT g.id_grupo, g.nome_grupo, g.destino_principal, g.data_inicio,
                       g.data_fim, g.orcamento, g.tipo_viagem, g.preferencias,
                       g.codigo_convite, u.nome AS criador
                FROM grupos_viagem g
                JOIN usuarios u ON g.criado_por = u.id_usuario
                WHERE g.id_grupo = %s
                """,
                (id_grupo,),
            )
            grupo = cursor.fetchone()
            if not grupo:
                raise HTTPException(status_code=404, detail="Grupo não encontrado")
            if grupo.get("orcamento") is not None:
                grupo["orcamento"] = float(grupo["orcamento"])
            return grupo
        finally:
            cursor.close()


def criar(dados, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            codigo_convite = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=6)
            )
            cursor.execute(
                """
                INSERT INTO grupos_viagem
                    (nome_grupo, destino_principal, data_inicio, data_fim,
                     orcamento, tipo_viagem, preferencias, criado_por, codigo_convite)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    dados.nome_grupo, dados.destino_principal, dados.data_inicio,
                    dados.data_fim, dados.orcamento, dados.tipo_viagem,
                    dados.preferencias, usuario_id, codigo_convite,
                ),
            )
            id_grupo = cursor.lastrowid
            cursor.execute(
                "INSERT INTO grupo_membros (id_grupo, id_usuario, cargo) VALUES (%s, %s, 'admin')",
                (id_grupo, usuario_id),
            )
            conexao.commit()
            return {
                "mensagem": "Grupo criado com sucesso",
                "id_grupo": id_grupo,
                "codigo_convite": codigo_convite,
            }
        finally:
            cursor.close()


def atualizar(id_grupo: int, dados) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute(
                """
                UPDATE grupos_viagem
                SET nome_grupo=%s, destino_principal=%s, data_inicio=%s, data_fim=%s,
                    orcamento=%s, tipo_viagem=%s, preferencias=%s
                WHERE id_grupo=%s
                """,
                (
                    dados.nome_grupo, dados.destino_principal, dados.data_inicio,
                    dados.data_fim, dados.orcamento, dados.tipo_viagem,
                    dados.preferencias, id_grupo,
                ),
            )
            conexao.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Grupo não encontrado")
            return {"mensagem": "Grupo atualizado"}
        finally:
            cursor.close()


def deletar(id_grupo: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("DELETE FROM gastos WHERE id_grupo=%s", (id_grupo,))
            cursor.execute("DELETE FROM roteiros WHERE id_grupo=%s", (id_grupo,))
            cursor.execute("DELETE FROM grupo_membros WHERE id_grupo=%s", (id_grupo,))
            cursor.execute("DELETE FROM chat_ia WHERE id_grupo=%s", (id_grupo,))

            cursor.execute("SELECT caminho_arquivo FROM fotos WHERE id_grupo=%s", (id_grupo,))
            fotos = cursor.fetchall()
            cursor.execute("DELETE FROM fotos WHERE id_grupo=%s", (id_grupo,))

            cursor.execute("DELETE FROM grupos_viagem WHERE id_grupo=%s", (id_grupo,))
            conexao.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Grupo não encontrado")

            # Limpeza de arquivos físicos após commit bem-sucedido
            for (caminho,) in fotos:
                caminho_fisico = os.path.join("uploads", os.path.basename(caminho))
                try:
                    if os.path.exists(caminho_fisico):
                        os.remove(caminho_fisico)
                except OSError:
                    pass

            return {"mensagem": "Grupo deletado"}
        finally:
            cursor.close()


def entrar_por_codigo(codigo: str, usuario_id: int) -> dict:
    codigo = codigo.strip().upper()
    if not codigo:
        raise HTTPException(status_code=400, detail="Código de convite inválido")

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_grupo, nome_grupo FROM grupos_viagem WHERE codigo_convite=%s",
                (codigo,),
            )
            grupo = cursor.fetchone()
            if not grupo:
                raise HTTPException(status_code=404, detail="Código de convite não encontrado")

            id_grupo = grupo["id_grupo"]
            cursor.execute(
                "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, usuario_id),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Você já é membro deste grupo")

            cursor.execute(
                "INSERT INTO grupo_membros (id_grupo, id_usuario, cargo) VALUES (%s, %s, 'membro')",
                (id_grupo, usuario_id),
            )
            conexao.commit()
            return {
                "mensagem": f"Você entrou no grupo '{grupo['nome_grupo']}'",
                "id_grupo": id_grupo,
            }
        finally:
            cursor.close()
