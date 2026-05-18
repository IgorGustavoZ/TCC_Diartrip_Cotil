from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import get_db
from utils.auth import get_usuario_logado

router = APIRouter()

class RoteiroInput(BaseModel):
    id_grupo: int
    titulo: str
    descricao: str

class RoteiroUpdate(BaseModel):
    titulo: str
    descricao: str

@router.get("/roteiros")
def listar_roteiros():
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT id_roteiro, id_grupo, titulo, descricao, data_criacao FROM roteiros")
        roteiros = cursor.fetchall()
        cursor.close()
        return roteiros

@router.get("/roteiros/{id_roteiro}")
def buscar_roteiro(id_roteiro: int):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_roteiro, id_grupo, titulo, descricao, data_criacao FROM roteiros WHERE id_roteiro=%s",
            (id_roteiro,)
        )
        roteiro = cursor.fetchone()
        cursor.close()
        if roteiro is None:
            raise HTTPException(status_code=404, detail="Roteiro não encontrado")
        return roteiro

@router.post("/roteiros")
def criar_roteiro(dados: RoteiroInput, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT 1 FROM grupos_viagem WHERE id_grupo=%s", (dados.id_grupo,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Grupo não existe")
        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (dados.id_grupo, usuario_id)
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=403, detail="Usuário não pertence ao grupo")
        cursor.execute(
            "INSERT INTO roteiros (id_grupo, titulo, descricao) VALUES (%s, %s, %s)",
            (dados.id_grupo, dados.titulo, dados.descricao)
        )
        conexao.commit()
        cursor.close()
        return {"mensagem": "Roteiro criado com sucesso"}

@router.put("/roteiros/{id_roteiro}")
def atualizar_roteiro(id_roteiro: int, dados: RoteiroUpdate, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id_grupo FROM roteiros WHERE id_roteiro=%s", (id_roteiro,))
        resultado = cursor.fetchone()
        if resultado is None:
            raise HTTPException(status_code=404, detail="Roteiro não encontrado")
        id_grupo = resultado[0]
        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=403, detail="Sem permissão")
        cursor.execute(
            "UPDATE roteiros SET titulo=%s, descricao=%s WHERE id_roteiro=%s",
            (dados.titulo, dados.descricao, id_roteiro)
        )
        conexao.commit()
        cursor.close()
        return {"mensagem": "Roteiro atualizado"}

@router.delete("/roteiros/{id_roteiro}")
def deletar_roteiro(id_roteiro: int, usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id_grupo FROM roteiros WHERE id_roteiro=%s", (id_roteiro,))
        resultado = cursor.fetchone()
        if resultado is None:
            raise HTTPException(status_code=404, detail="Roteiro não encontrado")
        id_grupo = resultado[0]
        cursor.execute(
            "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
            (id_grupo, usuario_id)
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=403, detail="Sem permissão")
        cursor.execute("DELETE FROM roteiros WHERE id_roteiro=%s", (id_roteiro,))
        conexao.commit()
        cursor.close()
        return {"mensagem": "Roteiro deletado com sucesso"}