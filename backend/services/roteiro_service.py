import re

from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo

# "Dia N" é texto livre dentro de `titulo` (nunca foi uma coluna separada —
# ver migration 011). Só é usado aqui para agrupar o reordenar por dia sem
# alterar o que já está salvo no banco.
_RE_DIA = re.compile(r"(?i)^dia\s+(\d+)\s*[·\-–—]")


def _dia_de(titulo: str | None) -> int | None:
    m = _RE_DIA.match((titulo or "").strip())
    return int(m.group(1)) if m else None


def listar_por_grupo(id_grupo: int, usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                "SELECT id_roteiro, id_grupo, titulo, descricao, origem_ia, ordem, data_criacao "
                "FROM roteiros WHERE id_grupo=%s ORDER BY ordem ASC, data_criacao ASC",
                (id_grupo,),
            )
            return [_com_origem_ia_bool(r) for r in cursor.fetchall()]
        finally:
            cursor.close()


def listar_por_usuario(usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT r.id_roteiro, r.id_grupo, r.titulo, r.descricao, r.origem_ia, r.ordem, r.data_criacao
                FROM roteiros r
                JOIN grupo_membros gm ON r.id_grupo = gm.id_grupo
                WHERE gm.id_usuario = %s
                """,
                (usuario_id,),
            )
            return [_com_origem_ia_bool(r) for r in cursor.fetchall()]
        finally:
            cursor.close()


def buscar_por_id(id_roteiro: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_roteiro, id_grupo, titulo, descricao, origem_ia, ordem, data_criacao "
                "FROM roteiros WHERE id_roteiro=%s",
                (id_roteiro,),
            )
            roteiro = cursor.fetchone()
            if not roteiro:
                raise HTTPException(status_code=404, detail="Roteiro não encontrado")
            checar_membro_grupo(cursor, roteiro["id_grupo"], usuario_id)
            return _com_origem_ia_bool(roteiro)
        finally:
            cursor.close()


def _com_origem_ia_bool(roteiro: dict) -> dict:
    roteiro["origem_ia"] = bool(roteiro.get("origem_ia"))
    return roteiro


def criar(dados, usuario_id: int, origem_ia: bool = False) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, dados.id_grupo, usuario_id)
            if cargo != "admin":
                raise HTTPException(
                    status_code=403, detail="Apenas administradores podem adicionar roteiros"
                )
            cursor.execute(
                "INSERT INTO roteiros (id_grupo, titulo, descricao, origem_ia, ordem) "
                "SELECT %s, %s, %s, %s, COALESCE(MAX(ordem), -1) + 1 "
                "FROM roteiros WHERE id_grupo=%s",
                (dados.id_grupo, dados.titulo, dados.descricao, origem_ia, dados.id_grupo),
            )
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
            return {"mensagem": "Roteiro deletado com sucesso"}
        finally:
            cursor.close()


def mover(id_roteiro: int, direcao: str, usuario_id: int) -> dict:
    """Troca a posição (campo `ordem`) de um item com seu vizinho imediato
    dentro do mesmo "dia" — o dia é extraído do próprio texto do título
    (_dia_de), já que não existe uma coluna de dia separada. Itens sem "Dia N"
    no título (ex.: itens manuais) formam seu próprio grupo (dia=None), então
    mover um item nunca mistura a ordem entre dias/grupos diferentes.
    """
    if direcao not in ("cima", "baixo"):
        raise HTTPException(status_code=400, detail="Direção inválida")

    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_grupo, titulo, ordem FROM roteiros WHERE id_roteiro=%s",
                (id_roteiro,),
            )
            atual = cursor.fetchone()
            if not atual:
                raise HTTPException(status_code=404, detail="Roteiro não encontrado")

            cargo = checar_membro_grupo(cursor, atual["id_grupo"], usuario_id)
            if cargo != "admin":
                raise HTTPException(
                    status_code=403, detail="Apenas administradores podem reordenar roteiros"
                )

            cursor.execute(
                "SELECT id_roteiro, titulo, ordem FROM roteiros WHERE id_grupo=%s "
                "ORDER BY ordem ASC, data_criacao ASC",
                (atual["id_grupo"],),
            )
            itens = cursor.fetchall()

            dia_atual = _dia_de(atual["titulo"])
            mesmo_dia = [i for i in itens if _dia_de(i["titulo"]) == dia_atual]
            posicao = next(
                idx for idx, i in enumerate(mesmo_dia) if i["id_roteiro"] == id_roteiro
            )

            alvo_idx = posicao - 1 if direcao == "cima" else posicao + 1
            if alvo_idx < 0 or alvo_idx >= len(mesmo_dia):
                return {"mensagem": "Item já está no limite"}

            alvo = mesmo_dia[alvo_idx]
            cursor.execute(
                "UPDATE roteiros SET ordem=%s WHERE id_roteiro=%s",
                (alvo["ordem"], id_roteiro),
            )
            cursor.execute(
                "UPDATE roteiros SET ordem=%s WHERE id_roteiro=%s",
                (atual["ordem"], alvo["id_roteiro"]),
            )
            return {"mensagem": "Ordem atualizada"}
        finally:
            cursor.close()
