from fastapi import HTTPException, Depends
from database import get_db
from utils.auth import get_usuario_logado


def checar_membro_grupo(cursor, id_grupo: int, usuario_id: int) -> str:
    """
    Verifica pertencimento ao grupo usando um cursor já aberto.
    Retorna o cargo ('admin' ou 'membro'). Lança 403 se não pertencer.
    Usar dentro de services para centralizar a lógica de permissão.
    """
    cursor.execute(
        "SELECT cargo FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
        (id_grupo, usuario_id),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="Você não pertence a este grupo")
    return row["cargo"] if isinstance(row, dict) else row[0]


def verificar_pertence_ao_grupo(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)) -> str:
    """
    FastAPI Dependency: verifica pertencimento via path param id_grupo.
    Retorna o cargo. Usar em rotas onde id_grupo está no path.
    """
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)
        finally:
            cursor.close()
    return cargo


def verificar_admin_do_grupo(cargo: str = Depends(verificar_pertence_ao_grupo)) -> bool:
    """
    FastAPI Dependency: exige cargo de admin.
    Encadeia com verificar_pertence_ao_grupo para reutilizar a query.
    """
    if cargo != "admin":
        raise HTTPException(
            status_code=403, detail="Apenas administradores podem realizar esta ação"
        )
    return True
