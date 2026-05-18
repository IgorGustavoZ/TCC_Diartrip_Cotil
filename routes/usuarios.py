from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import get_db
from utils.security import gerar_hash
from utils.auth import get_usuario_logado

router = APIRouter()

class UsuarioInput(BaseModel):
    nome: str
    email: str
    senha: str

class UsuarioUpdate(BaseModel):
    nome: str
    email: str

@router.get("/usuarios")
def listar_usuarios(usuario_id: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT id_usuario, nome, email, foto_perfil, data_criacao FROM usuarios")
        usuarios = cursor.fetchall()
        cursor.close()
        return usuarios

@router.get("/usuarios/{id_usuario}")
def buscar_usuario(id_usuario: int, usuario_logado: int = Depends(get_usuario_logado)):
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_usuario, nome, email, foto_perfil, data_criacao FROM usuarios WHERE id_usuario=%s",
            (id_usuario,)
        )
        usuario = cursor.fetchone()
        cursor.close()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

@router.post("/usuarios")
def criar_usuario(dados: UsuarioInput):
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id_usuario FROM usuarios WHERE email=%s", (dados.email,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        senha_hash = gerar_hash(dados.senha)
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)",
            (dados.nome, dados.email, senha_hash)
        )
        conexao.commit()
        cursor.close()
    return {"mensagem": "Usuário criado com sucesso"}

@router.put("/usuarios/{id_usuario}")
def atualizar_usuario(
    id_usuario: int,
    dados: UsuarioUpdate,
    usuario_logado: int = Depends(get_usuario_logado)
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute(
            "UPDATE usuarios SET nome=%s, email=%s WHERE id_usuario=%s",
            (dados.nome, dados.email, id_usuario)
        )
        conexao.commit()
        if cursor.rowcount == 0:
            cursor.close()
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        cursor.close()
    return {"mensagem": "Usuário atualizado"}

@router.delete("/usuarios/{id_usuario}")
def deletar_usuario(
    id_usuario: int,
    usuario_logado: int = Depends(get_usuario_logado)
):
    if usuario_logado != id_usuario:
        raise HTTPException(status_code=403, detail="Sem permissão")
    with get_db() as conexao:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id_usuario=%s", (id_usuario,))
        conexao.commit()
        if cursor.rowcount == 0:
            cursor.close()
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        cursor.close()
    return {"mensagem": "Usuário deletado"}