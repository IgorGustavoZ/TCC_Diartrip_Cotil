"""Schema inicial do Diartrip

Revision ID: 001
Revises:
Create Date: 2026-06-16

Cria todas as tabelas base do sistema na ordem correta (respeitando FKs).
Esta migration representa o estado inicial do banco antes de qualquer melhoria.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario   INT          NOT NULL AUTO_INCREMENT,
            nome         VARCHAR(100) NOT NULL,
            email        VARCHAR(255) NOT NULL,
            senha_hash   VARCHAR(255) NOT NULL,
            bio          TEXT         NULL,
            foto_perfil  TEXT         NULL,
            data_criacao TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_usuario),
            UNIQUE KEY uq_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS grupos_viagem (
            id_grupo          INT           NOT NULL AUTO_INCREMENT,
            nome_grupo        VARCHAR(150)  NOT NULL,
            destino_principal VARCHAR(200)  NULL,
            data_inicio       DATE          NULL,
            data_fim          DATE          NULL,
            orcamento         DECIMAL(12,2) NULL,
            tipo_viagem       VARCHAR(100)  NULL,
            preferencias      TEXT          NULL,
            codigo_convite    VARCHAR(10)   NOT NULL,
            criado_por        INT           NOT NULL,
            PRIMARY KEY (id_grupo),
            UNIQUE KEY uq_codigo_convite (codigo_convite),
            FULLTEXT KEY ft_nome_grupo (nome_grupo),
            CONSTRAINT fk_gv_criador FOREIGN KEY (criado_por)
                REFERENCES usuarios (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS grupo_membros (
            id         INT    NOT NULL AUTO_INCREMENT,
            id_grupo   INT    NOT NULL,
            id_usuario INT    NOT NULL,
            cargo      ENUM('admin','membro') NOT NULL DEFAULT 'membro',
            PRIMARY KEY (id),
            UNIQUE KEY uq_grupo_usuario (id_grupo, id_usuario),
            CONSTRAINT fk_gm_grupo   FOREIGN KEY (id_grupo)   REFERENCES grupos_viagem (id_grupo)  ON DELETE CASCADE,
            CONSTRAINT fk_gm_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios      (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS roteiros (
            id_roteiro   INT          NOT NULL AUTO_INCREMENT,
            id_grupo     INT          NOT NULL,
            titulo       VARCHAR(200) NOT NULL,
            descricao    TEXT         NULL,
            data_criacao TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_roteiro),
            KEY idx_roteiros_grupo (id_grupo),
            CONSTRAINT fk_rot_grupo FOREIGN KEY (id_grupo)
                REFERENCES grupos_viagem (id_grupo) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id_gasto   INT           NOT NULL AUTO_INCREMENT,
            id_grupo   INT           NOT NULL,
            id_usuario INT           NOT NULL,
            valor      DECIMAL(12,2) NOT NULL,
            categoria  VARCHAR(100)  NULL,
            descricao  VARCHAR(500)  NULL,
            data_gasto DATE          NOT NULL DEFAULT (CURRENT_DATE),
            PRIMARY KEY (id_gasto),
            KEY idx_gastos_grupo (id_grupo),
            CONSTRAINT fk_gasto_grupo   FOREIGN KEY (id_grupo)   REFERENCES grupos_viagem (id_grupo)  ON DELETE CASCADE,
            CONSTRAINT fk_gasto_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios      (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS divisao_gastos (
            id             INT           NOT NULL AUTO_INCREMENT,
            id_gasto       INT           NOT NULL,
            id_usuario     INT           NOT NULL,
            valor_dividido DECIMAL(12,2) NOT NULL,
            PRIMARY KEY (id),
            KEY idx_divisao_gasto   (id_gasto),
            KEY idx_divisao_usuario (id_usuario),
            CONSTRAINT fk_div_gasto   FOREIGN KEY (id_gasto)   REFERENCES gastos   (id_gasto)   ON DELETE CASCADE,
            CONSTRAINT fk_div_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS fotos (
            id_foto         INT          NOT NULL AUTO_INCREMENT,
            id_grupo        INT          NOT NULL,
            id_usuario      INT          NOT NULL,
            caminho_arquivo TEXT         NOT NULL,
            template_usado  VARCHAR(100) NULL,
            data_upload     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_foto),
            KEY idx_fotos_grupo (id_grupo),
            CONSTRAINT fk_foto_grupo   FOREIGN KEY (id_grupo)   REFERENCES grupos_viagem (id_grupo)  ON DELETE CASCADE,
            CONSTRAINT fk_foto_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios      (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS chat_ia (
            id_chat        INT       NOT NULL AUTO_INCREMENT,
            id_usuario     INT       NOT NULL,
            id_grupo       INT       NOT NULL,
            pergunta       TEXT      NOT NULL,
            resposta       TEXT      NULL,
            data_interacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_chat),
            KEY idx_chatia_usuario (id_usuario),
            KEY idx_chatia_grupo   (id_grupo),
            CONSTRAINT fk_chatia_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios      (id_usuario) ON DELETE CASCADE,
            CONSTRAINT fk_chatia_grupo   FOREIGN KEY (id_grupo)   REFERENCES grupos_viagem (id_grupo)   ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS mensagens_grupo (
            id_mensagem INT       NOT NULL AUTO_INCREMENT,
            id_grupo    INT       NOT NULL,
            id_usuario  INT       NOT NULL,
            conteudo    TEXT      NOT NULL,
            data_envio  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_mensagem),
            KEY idx_msg_grupo    (id_grupo),
            KEY idx_msg_grupo_id (id_grupo, id_mensagem),
            CONSTRAINT fk_msg_grupo   FOREIGN KEY (id_grupo)   REFERENCES grupos_viagem (id_grupo)  ON DELETE CASCADE,
            CONSTRAINT fk_msg_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios      (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id_post      INT       NOT NULL AUTO_INCREMENT,
            id_usuario   INT       NOT NULL,
            conteudo     TEXT      NOT NULL,
            imagem       TEXT      NULL,
            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_post),
            KEY idx_posts_usuario (id_usuario),
            CONSTRAINT fk_post_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS post_curtidas (
            id           INT       NOT NULL AUTO_INCREMENT,
            id_post      INT       NOT NULL,
            id_usuario   INT       NOT NULL,
            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uq_curtida (id_post, id_usuario),
            CONSTRAINT fk_curt_post    FOREIGN KEY (id_post)    REFERENCES posts    (id_post)    ON DELETE CASCADE,
            CONSTRAINT fk_curt_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS post_comentarios (
            id           INT       NOT NULL AUTO_INCREMENT,
            id_post      INT       NOT NULL,
            id_usuario   INT       NOT NULL,
            conteudo     TEXT      NOT NULL,
            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_coment_post (id_post),
            CONSTRAINT fk_coment_post    FOREIGN KEY (id_post)    REFERENCES posts    (id_post)    ON DELETE CASCADE,
            CONSTRAINT fk_coment_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS seguidores (
            id           INT       NOT NULL AUTO_INCREMENT,
            id_seguidor  INT       NOT NULL,
            id_seguido   INT       NOT NULL,
            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uq_seguidor_seguido (id_seguidor, id_seguido),
            CONSTRAINT fk_seg_seguidor FOREIGN KEY (id_seguidor) REFERENCES usuarios (id_usuario) ON DELETE CASCADE,
            CONSTRAINT fk_seg_seguido  FOREIGN KEY (id_seguido)  REFERENCES usuarios (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))")


def downgrade() -> None:
    for tabela in [
        "seguidores", "post_comentarios", "post_curtidas", "posts",
        "mensagens_grupo", "chat_ia", "fotos", "divisao_gastos",
        "gastos", "roteiros", "grupo_membros", "grupos_viagem", "usuarios",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {tabela}")
