from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import get_db
from utils.auth import get_usuario_logado

router = APIRouter()

class MembroInput(BaseModel):
    id_usuario_novo: int

@router.get("/grupos/{id_grupo}/membros")
def listar_membros(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=403, detail="Acesso negado")
        cursor.execute("""
            SELECT u.id_usuario, u.nome, gm.cargo
            FROM grupo_membros gm
            JOIN usuarios u ON gm.id_usuario = u.id_usuario
            WHERE gm.id_grupo = %s
        """, (id_grupo,))
        membros = cursor.fetchall()
        cursor.close()
        return membros

@router.post("/grupos/{id_grupo}/membros")
def adicionar_membro(id_grupo: int, dados: MembroInput, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        membro = cursor.fetchone()
        if not membro or membro[0] != "admin":
            raise HTTPException(status_code=403, detail="Apenas admin pode adicionar")
        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, dados.id_usuario_novo)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Usuário já está no grupo")
        cursor.execute(
            "INSERT INTO grupo_membros (id_grupo, id_usuario) VALUES (%s, %s)",
            (id_grupo, dados.id_usuario_novo)
        )
        conexao.commit()
        cursor.close()
        return {"mensagem": "Membro adicionado"}

@router.delete("/grupos/{id_grupo}/membros/{id_usuario_remover}")
def remover_membro(id_grupo: int, id_usuario_remover: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        atual = cursor.fetchone()
        if not atual:
            raise HTTPException(status_code=403, detail="Você não pertence ao grupo")
        if usuario_id != id_usuario_remover and atual[0] != "admin":
            raise HTTPException(status_code=403, detail="Sem permissão")
        cursor.execute(
            "DELETE FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, id_usuario_remover)
        )
        conexao.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Membro não encontrado")
        cursor.close()
        return {"mensagem": "Membro removido"}

@router.put("/grupos/{id_grupo}/membros/{id_usuario_promover}")
def promover_admin(id_grupo: int, id_usuario_promover: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        atual = cursor.fetchone()
        if not atual or atual[0] != "admin":
            raise HTTPException(status_code=403, detail="Apenas admin pode promover")
        cursor.execute(
            "UPDATE grupo_membros SET cargo='admin' WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, id_usuario_promover)
        )
        conexao.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Membro não encontrado")
        cursor.close()
        return {"mensagem": "Usuário promovido a admin"}

@router.delete("/grupos/{id_grupo}/sair")
def sair_grupo(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "DELETE FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        conexao.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Você não está no grupo")
        cursor.close()
        return {"mensagem": "Saiu do grupo"}