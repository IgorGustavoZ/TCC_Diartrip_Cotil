from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from database import get_db
from utils.auth import get_usuario_logado

router = APIRouter()

class GrupoInput(BaseModel):
    nome_grupo: str
    destino_principal: str

@router.get("/grupos")
def listar_grupos(usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("""
            SELECT g.id_grupo, g.nome_grupo, g.destino_principal, g.data_inicio, g.data_fim, u.nome AS criador
            FROM grupos_viagem g
            JOIN usuarios u ON g.criado_por = u.id_usuario
            JOIN grupo_membros gm ON gm.id_grupo = g.id_grupo
            WHERE gm.id_usuario = %s
        """, (usuario_id,))
        grupos = cursor.fetchall()
        cursor.close()
        return grupos

# ROTA FIXA PRIMEIRO
@router.get("/grupos/buscar")
def buscar_grupo_por_nome(
    nome: str | None = Query(None),
    usuario_id: int = Depends(get_usuario_logado)
):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT g.id_grupo, g.nome_grupo, g.destino_principal, g.data_inicio, g.data_fim, u.nome AS criador
            FROM grupos_viagem g
            JOIN usuarios u ON g.criado_por = u.id_usuario
            JOIN grupo_membros gm ON gm.id_grupo = g.id_grupo
            WHERE gm.id_usuario = %s
        """

        params = [usuario_id]

        if nome:
            sql += " AND g.nome_grupo LIKE %s"
            params.append(f"%{nome}%")

        cursor.execute(sql, tuple(params))

        grupos = cursor.fetchall()
        cursor.close()

        return grupos

# ROTA DINÂMICA DEPOIS
@router.get("/grupos/{id_grupo}")
def buscar_grupo_por_id(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )

        if cursor.fetchone() is None:
            cursor.close()
            raise HTTPException(status_code=403, detail="Acesso negado")

        cursor.execute("""
            SELECT g.id_grupo, g.nome_grupo, g.destino_principal, g.data_inicio, g.data_fim, u.nome AS criador
            FROM grupos_viagem g
            JOIN usuarios u ON g.criado_por = u.id_usuario
            WHERE g.id_grupo = %s
        """, (id_grupo,))

        grupo = cursor.fetchone()
        cursor.close()

        if not grupo:
            raise HTTPException(status_code=404, detail="Grupo não encontrado")

        return grupo

@router.post("/grupos")
def criar_grupo(dados: GrupoInput, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()

        cursor.execute(
            "INSERT INTO grupos_viagem(nome_grupo, destino_principal, criado_por) VALUES (%s, %s, %s)",
            (dados.nome_grupo, dados.destino_principal, usuario_id)
        )

        id_grupo = cursor.lastrowid

        cursor.execute(
            "INSERT INTO grupo_membros (id_grupo, id_usuario, cargo) VALUES (%s, %s, 'admin')",
            (id_grupo, usuario_id)
        )

        conexao.commit()
        cursor.close()

        return {
            "mensagem": "Grupo criado com sucesso",
            "id_grupo": id_grupo
        }

@router.put("/grupos/{id_grupo}")
def atualizar_grupo(id_grupo: int, dados: GrupoInput, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )

        membro = cursor.fetchone()

        if not membro or membro[0] != "admin":
            cursor.close()
            raise HTTPException(status_code=403, detail="Apenas admin pode editar o grupo")

        cursor.execute(
            "UPDATE grupos_viagem SET nome_grupo=%s, destino_principal=%s WHERE id_grupo=%s",
            (dados.nome_grupo, dados.destino_principal, id_grupo)
        )

        conexao.commit()

        if cursor.rowcount == 0:
            cursor.close()
            raise HTTPException(status_code=404, detail="Grupo não encontrado")

        cursor.close()

        return {"mensagem": "Grupo atualizado"}

@router.delete("/grupos/{id_grupo}")
def deletar_grupo(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )

        membro = cursor.fetchone()

        if not membro or membro[0] != "admin":
            cursor.close()
            raise HTTPException(status_code=403, detail="Apenas admin pode deletar o grupo")

        cursor.execute(
            "DELETE FROM grupos_viagem WHERE id_grupo=%s",
            (id_grupo,)
        )

        conexao.commit()

        if cursor.rowcount == 0:
            cursor.close()
            raise HTTPException(status_code=404, detail="Grupo não encontrado")

        cursor.close()

        return {"mensagem": "Grupo deletado"}