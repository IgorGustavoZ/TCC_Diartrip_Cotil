import secrets
import string
from datetime import datetime, timedelta, timezone
from mysql.connector import Error, IntegrityError
from fastapi import HTTPException
from database import get_db
from utils.dependencies import checar_membro_grupo
from utils.cloudinary_upload import deletar_imagem

def listar_por_usuario(usuario_id: int) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT g.id_grupo, g.nome_grupo, g.destino_principal,
                       g.data_inicio, g.data_fim, u.nome AS criador
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


def buscar_por_nome(usuario_id: int, nome: str | None, limite: int = 50, offset: int = 0) -> list:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            sql = """
                SELECT g.id_grupo, g.nome_grupo, g.destino_principal,
                       g.data_inicio, g.data_fim, u.nome AS criador
                FROM grupos_viagem g
                JOIN usuarios u ON g.criado_por = u.id_usuario
                JOIN grupo_membros gm ON gm.id_grupo = g.id_grupo
                WHERE gm.id_usuario = %s
            """
            params: list = [usuario_id]
            if nome:
                nome_safe = nome.strip()
                if len(nome_safe) >= 3:
                    sql += " AND MATCH(g.nome_grupo) AGAINST(%s IN BOOLEAN MODE)"
                    params.append(f"+{nome_safe}*")
                else:
                    sql += " AND g.nome_grupo LIKE %s"
                    params.append(f"%{nome_safe}%")
            sql += " LIMIT %s OFFSET %s"
            params.extend([limite, offset])
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()


def buscar_por_id(id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)
            cursor.execute(
                """
                SELECT g.id_grupo, g.nome_grupo, g.destino_principal, g.data_inicio,
                       g.data_fim, g.orcamento, g.tipo_viagem, g.preferencias,
                       g.criado_por AS criador_id, u.nome AS criador,
                       g.publica, g.limite_participantes,
                       (SELECT COUNT(*) FROM grupo_membros gm WHERE gm.id_grupo = g.id_grupo) AS vagas_ocupadas
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
            grupo["publica"] = bool(grupo.get("publica"))
            if cargo == "admin":
                cursor.execute(
                    "SELECT codigo_convite FROM grupos_viagem WHERE id_grupo=%s", (id_grupo,)
                )
                row = cursor.fetchone()
                grupo["codigo_convite"] = row["codigo_convite"] if row else None
            return grupo
        finally:
            cursor.close()


def obter_codigo_convite(id_grupo: int, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)
            if cargo != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="Apenas administradores podem ver o código de convite",
                )
            cursor.execute(
                "SELECT codigo_convite FROM grupos_viagem WHERE id_grupo=%s", (id_grupo,)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Grupo não encontrado")
            return {"codigo_convite": row["codigo_convite"]}
        finally:
            cursor.close()


def _gerar_codigo() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(6))


def criar(dados, usuario_id: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            for _ in range(5):
                codigo_convite = _gerar_codigo()
                try:
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
                    break
                except IntegrityError as e:
                    if e.errno == 1062:
                        conexao.rollback()
                        continue
                    raise
            else:
                raise HTTPException(status_code=503, detail="Não foi possível gerar código único. Tente novamente.")

            id_grupo = cursor.lastrowid
            cursor.execute(
                "INSERT INTO grupo_membros (id_grupo, id_usuario, cargo) VALUES (%s, %s, 'admin')",
                (id_grupo, usuario_id),
            )
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
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Grupo não encontrado")
            return {"mensagem": "Grupo atualizado"}
        finally:
            cursor.close()


def deletar(id_grupo: int) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT 1 FROM grupos_viagem WHERE id_grupo=%s", (id_grupo,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Grupo não encontrado")

            cursor.execute("SELECT caminho_arquivo FROM fotos WHERE id_grupo=%s", (id_grupo,))
            fotos = [row[0] for row in cursor.fetchall()]

            cursor.execute("DELETE FROM grupos_viagem WHERE id_grupo=%s", (id_grupo,))

            for url in fotos:
                deletar_imagem(url)

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
                "SELECT id_grupo, nome_grupo, codigo_validade FROM grupos_viagem WHERE codigo_convite=%s",
                (codigo,),
            )
            grupo = cursor.fetchone()
            if not grupo:
                raise HTTPException(status_code=404, detail="Código de convite não encontrado")

            if grupo.get("codigo_validade") is not None:
                validade = grupo["codigo_validade"]
                if isinstance(validade, datetime) and validade.tzinfo is None:
                    validade = validade.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > validade:
                    raise HTTPException(
                        status_code=410,
                        detail="Este código de convite expirou. Solicite um novo ao administrador do grupo.",
                    )

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
            return {
                "mensagem": f"Você entrou no grupo '{grupo['nome_grupo']}'",
                "id_grupo": id_grupo,
            }
        finally:
            cursor.close()


def rotacionar_codigo_convite(id_grupo: int, usuario_id: int, validade_dias: int = 7) -> dict:
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cargo = checar_membro_grupo(cursor, id_grupo, usuario_id)
            if cargo != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="Apenas administradores podem rotacionar o código de convite",
                )

            nova_validade = datetime.now(timezone.utc) + timedelta(days=validade_dias)

            for _ in range(5):
                novo_codigo = _gerar_codigo()
                try:
                    cursor.execute(
                        "UPDATE grupos_viagem SET codigo_convite=%s, codigo_validade=%s WHERE id_grupo=%s",
                        (novo_codigo, nova_validade, id_grupo),
                    )
                    break
                except IntegrityError as e:
                    if e.errno == 1062:
                        conexao.rollback()
                        continue
                    raise
            else:
                raise HTTPException(status_code=503, detail="Não foi possível gerar código único.")

            return {"codigo_convite": novo_codigo}
        finally:
            cursor.close()
