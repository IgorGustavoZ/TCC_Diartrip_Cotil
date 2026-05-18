from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import get_db
from utils.auth import get_usuario_logado

router = APIRouter()

class GastoInput(BaseModel):
    valor: float
    categoria: str
    descricao: Optional[str] = None
    data_gasto: Optional[str] = None

class GastoUpdate(BaseModel):
    valor: float
    categoria: str
    descricao: str

@router.get("/grupos/{id_grupo}/gastos")
def listar_gastos(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=403, detail="Acesso negado")
        cursor.execute("""
            SELECT g.id_gasto, g.valor, g.categoria, g.descricao, g.data_gasto, u.nome
            FROM gastos g
            JOIN usuarios u ON g.id_usuario = u.id_usuario
            WHERE g.id_grupo = %s
            ORDER BY g.data_gasto DESC
        """, (id_grupo,))
        gastos = cursor.fetchall()
        cursor.close()
        return gastos

@router.post("/grupos/{id_grupo}/gastos")
def criar_gasto(
    id_grupo: int,
    dados: GastoInput,
    usuario_id: int = Depends(get_usuario_logado)
):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=403, detail="Você não pertence ao grupo")
        cursor.execute("""
            INSERT INTO gastos (id_grupo, id_usuario, valor, categoria, descricao, data_gasto)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_grupo, usuario_id, dados.valor, dados.categoria, dados.descricao, dados.data_gasto))
        conexao.commit()
        cursor.close()
        return {"mensagem": "Gasto registrado"}

@router.put("/gastos/{id_gasto}")
def atualizar_gasto(
    id_gasto: int,
    dados: GastoUpdate,
    usuario_id: int = Depends(get_usuario_logado)
):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id_usuario, id_grupo FROM gastos WHERE id_gasto=%s",
            (id_gasto,)
        )
        gasto = cursor.fetchone()
        if not gasto:
            raise HTTPException(status_code=404, detail="Gasto não encontrado")
        dono_id, id_grupo = gasto
        cursor.execute(
            "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        membro = cursor.fetchone()
        if not membro:
            raise HTTPException(status_code=403, detail="Acesso negado")
        if usuario_id != dono_id and membro[0] != "admin":
            raise HTTPException(status_code=403, detail="Sem permissão")
        cursor.execute("""
            UPDATE gastos SET valor=%s, categoria=%s, descricao=%s WHERE id_gasto=%s
        """, (dados.valor, dados.categoria, dados.descricao, id_gasto))
        conexao.commit()
        cursor.close()
        return {"mensagem": "Gasto atualizado"}

@router.delete("/gastos/{id_gasto}")
def deletar_gasto(id_gasto: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT id_usuario, id_grupo FROM gastos WHERE id_gasto=%s",
            (id_gasto,)
        )
        gasto = cursor.fetchone()
        if not gasto:
            raise HTTPException(status_code=404, detail="Gasto não encontrado")
        dono_id, id_grupo = gasto
        cursor.execute(
            "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        membro = cursor.fetchone()
        if not membro:
            raise HTTPException(status_code=403, detail="Acesso negado")
        if usuario_id != dono_id and membro[0] != "admin":
            raise HTTPException(status_code=403, detail="Sem permissão")
        cursor.execute("DELETE FROM gastos WHERE id_gasto=%s", (id_gasto,))
        conexao.commit()
        cursor.close()
        return {"mensagem": "Gasto removido"}