from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo

_SELECT_EXPLORAR = """
    SELECT g.id_grupo, g.nome_grupo, g.destino_principal, g.data_inicio, g.data_fim,
           g.criado_por AS id_criador, u.nome AS criador, g.limite_participantes,
           (SELECT COUNT(*) FROM grupo_membros gm WHERE gm.id_grupo = g.id_grupo) AS vagas_ocupadas
    FROM grupos_viagem g
    JOIN usuarios u ON g.criado_por = u.id_usuario
    WHERE g.publica = 1
"""


def publicar(id_grupo: int, publica: bool, limite_participantes: int | None) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            if publica:
                if not limite_participantes or limite_participantes < 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Informe um limite de participantes válido (mínimo 1) para publicar a viagem",
                    )
                cursor.execute(
                    "SELECT COUNT(*) AS total FROM grupo_membros WHERE id_grupo=%s", (id_grupo,)
                )
                membros_atuais = cursor.fetchone()["total"]
                if limite_participantes < membros_atuais:
                    raise HTTPException(
                        status_code=400,
                        detail=f"O limite não pode ser menor que o número atual de participantes ({membros_atuais})",
                    )
                cursor.execute(
                    "UPDATE grupos_viagem SET publica=1, limite_participantes=%s WHERE id_grupo=%s",
                    (limite_participantes, id_grupo),
                )
                mensagem = "Viagem publicada em Explorar Viagens"
            else:
                cursor.execute(
                    "UPDATE grupos_viagem SET publica=0 WHERE id_grupo=%s",
                    (id_grupo,),
                )
                mensagem = "Viagem removida de Explorar Viagens"

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Grupo não encontrado")
            return {"mensagem": mensagem}
        finally:
            cursor.close()


def listar_publicas(destino: str | None, limite: int = 20, offset: int = 0) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            sql = _SELECT_EXPLORAR
            params: list = []
            if destino:
                destino_safe = destino.strip()
                if len(destino_safe) >= 3:
                    sql += " AND (MATCH(g.nome_grupo) AGAINST(%s IN BOOLEAN MODE) OR g.destino_principal LIKE %s)"
                    params.extend([f"+{destino_safe}*", f"%{destino_safe}%"])
                else:
                    sql += " AND (g.nome_grupo LIKE %s OR g.destino_principal LIKE %s)"
                    params.extend([f"%{destino_safe}%", f"%{destino_safe}%"])
            sql += " ORDER BY g.data_criacao DESC LIMIT %s OFFSET %s"
            params.extend([limite, offset])
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()


def detalhar_publica(id_grupo: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(_SELECT_EXPLORAR + " AND g.id_grupo = %s", (id_grupo,))
            grupo = cursor.fetchone()
            if not grupo:
                raise HTTPException(status_code=404, detail="Viagem pública não encontrada")
            return grupo
        finally:
            cursor.close()


def solicitar(id_grupo: int, usuario_id: int, mensagem: str | None) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT limite_participantes FROM grupos_viagem WHERE id_grupo=%s AND publica=1",
                (id_grupo,),
            )
            grupo = cursor.fetchone()
            if not grupo:
                raise HTTPException(status_code=404, detail="Viagem pública não encontrada")

            cursor.execute(
                "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, usuario_id),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Você já é membro desta viagem")

            cursor.execute(
                """
                SELECT 1 FROM viagem_solicitacoes
                WHERE id_grupo=%s AND id_usuario_solicitante=%s AND status='pendente'
                """,
                (id_grupo, usuario_id),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Você já solicitou participação nesta viagem")

            cursor.execute(
                "SELECT COUNT(*) AS total FROM grupo_membros WHERE id_grupo=%s", (id_grupo,)
            )
            ocupadas = cursor.fetchone()["total"]
            if grupo["limite_participantes"] is not None and ocupadas >= grupo["limite_participantes"]:
                raise HTTPException(status_code=409, detail="Viagem lotada")

            mensagem_limpa = (mensagem or "").strip() or None
            cursor.execute(
                "INSERT INTO viagem_solicitacoes (id_grupo, id_usuario_solicitante, mensagem) VALUES (%s, %s, %s)",
                (id_grupo, usuario_id, mensagem_limpa),
            )
            return {"mensagem": "Solicitação de participação enviada", "id_solicitacao": cursor.lastrowid}
        finally:
            cursor.close()


def listar_solicitacoes(id_grupo: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT s.id_solicitacao, s.id_grupo, g.nome_grupo,
                       s.id_usuario_solicitante, u.nome, u.foto_perfil,
                       s.mensagem, s.status, s.data_solicitacao
                FROM viagem_solicitacoes s
                JOIN grupos_viagem g ON s.id_grupo = g.id_grupo
                JOIN usuarios u ON s.id_usuario_solicitante = u.id_usuario
                WHERE s.id_grupo=%s AND s.status='pendente'
                ORDER BY s.data_solicitacao ASC
                """,
                (id_grupo,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def _checar_admin_da_solicitacao(cursor, id_solicitacao: int, usuario_id: int) -> dict:
    cursor.execute(
        """
        SELECT id_grupo, id_usuario_solicitante, status
        FROM viagem_solicitacoes WHERE id_solicitacao=%s FOR UPDATE
        """,
        (id_solicitacao,),
    )
    solicitacao = cursor.fetchone()
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    cargo = checar_membro_grupo(cursor, solicitacao["id_grupo"], usuario_id)
    if cargo != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem responder solicitações")
    if solicitacao["status"] != "pendente":
        raise HTTPException(status_code=409, detail="Esta solicitação já foi respondida")
    return solicitacao


def aceitar_solicitacao(id_solicitacao: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            solicitacao = _checar_admin_da_solicitacao(cursor, id_solicitacao, usuario_id)
            id_grupo = solicitacao["id_grupo"]
            id_solicitante = solicitacao["id_usuario_solicitante"]

            cursor.execute(
                "SELECT limite_participantes FROM grupos_viagem WHERE id_grupo=%s FOR UPDATE",
                (id_grupo,),
            )
            limite_row = cursor.fetchone()
            limite = limite_row["limite_participantes"] if limite_row else None

            cursor.execute(
                "SELECT 1 FROM grupo_membros WHERE id_grupo=%s AND id_usuario=%s",
                (id_grupo, id_solicitante),
            )
            ja_membro = cursor.fetchone() is not None

            if not ja_membro:
                if limite is not None:
                    cursor.execute(
                        "SELECT COUNT(*) AS total FROM grupo_membros WHERE id_grupo=%s FOR UPDATE",
                        (id_grupo,),
                    )
                    ocupadas = cursor.fetchone()["total"]
                    if ocupadas >= limite:
                        raise HTTPException(
                            status_code=409,
                            detail="Viagem lotada — não é possível aceitar mais participantes",
                        )
                cursor.execute(
                    "INSERT INTO grupo_membros (id_grupo, id_usuario) VALUES (%s, %s)",
                    (id_grupo, id_solicitante),
                )

            cursor.execute(
                """
                UPDATE viagem_solicitacoes
                SET status='aceita', data_resposta=CURRENT_TIMESTAMP, respondido_por=%s
                WHERE id_solicitacao=%s
                """,
                (usuario_id, id_solicitacao),
            )
            return {"mensagem": "Solicitação aceita. Usuário adicionado à viagem."}
        finally:
            cursor.close()


def recusar_solicitacao(id_solicitacao: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            _checar_admin_da_solicitacao(cursor, id_solicitacao, usuario_id)
            cursor.execute(
                """
                UPDATE viagem_solicitacoes
                SET status='recusada', data_resposta=CURRENT_TIMESTAMP, respondido_por=%s
                WHERE id_solicitacao=%s
                """,
                (usuario_id, id_solicitacao),
            )
            return {"mensagem": "Solicitação recusada"}
        finally:
            cursor.close()
