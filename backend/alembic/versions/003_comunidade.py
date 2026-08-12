"""Comunidade pública de viagens

Revision ID: 003
Revises: 002
Create Date: 2026-08-11

Cria as tabelas dedicadas à funcionalidade de Comunidade Pública de Viagens:
publicação pública de uma viagem existente, curtidas, comentários e
solicitações de participação. Nenhuma tabela existente é alterada — a
publicação referencia grupos_viagem/usuarios apenas por FK.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS viagem_publicacoes (
            id_publicacao      INT       NOT NULL AUTO_INCREMENT,
            id_grupo            INT       NOT NULL,
            id_usuario          INT       NOT NULL,
            descricao           TEXT      NULL,
            ativo               TINYINT(1) NOT NULL DEFAULT 1,
            data_publicacao     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data_despublicacao  TIMESTAMP NULL DEFAULT NULL,
            PRIMARY KEY (id_publicacao),
            UNIQUE KEY uq_publicacao_grupo (id_grupo),
            KEY idx_pub_ativo_data (ativo, data_publicacao DESC),
            CONSTRAINT fk_pub_grupo   FOREIGN KEY (id_grupo)   REFERENCES grupos_viagem (id_grupo)  ON DELETE CASCADE,
            CONSTRAINT fk_pub_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios      (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS viagem_publicacao_curtidas (
            id            INT       NOT NULL AUTO_INCREMENT,
            id_publicacao INT       NOT NULL,
            id_usuario    INT       NOT NULL,
            data_criacao  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uq_pub_curtida (id_publicacao, id_usuario),
            CONSTRAINT fk_pubcurt_publicacao FOREIGN KEY (id_publicacao) REFERENCES viagem_publicacoes (id_publicacao) ON DELETE CASCADE,
            CONSTRAINT fk_pubcurt_usuario    FOREIGN KEY (id_usuario)    REFERENCES usuarios            (id_usuario)    ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS viagem_publicacao_comentarios (
            id            INT       NOT NULL AUTO_INCREMENT,
            id_publicacao INT       NOT NULL,
            id_usuario    INT       NOT NULL,
            conteudo      TEXT      NOT NULL,
            data_criacao  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_pubcoment_publicacao (id_publicacao),
            CONSTRAINT fk_pubcoment_publicacao FOREIGN KEY (id_publicacao) REFERENCES viagem_publicacoes (id_publicacao) ON DELETE CASCADE,
            CONSTRAINT fk_pubcoment_usuario    FOREIGN KEY (id_usuario)    REFERENCES usuarios            (id_usuario)    ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS viagem_solicitacoes (
            id_solicitacao         INT       NOT NULL AUTO_INCREMENT,
            id_grupo                INT       NOT NULL,
            id_usuario_solicitante  INT       NOT NULL,
            status                  ENUM('pendente','aceita','recusada') NOT NULL DEFAULT 'pendente',
            mensagem                VARCHAR(500) NULL,
            data_solicitacao        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data_resposta           TIMESTAMP NULL DEFAULT NULL,
            respondido_por          INT       NULL,
            PRIMARY KEY (id_solicitacao),
            KEY idx_solic_grupo_status (id_grupo, status),
            CONSTRAINT fk_solic_grupo        FOREIGN KEY (id_grupo)               REFERENCES grupos_viagem (id_grupo)  ON DELETE CASCADE,
            CONSTRAINT fk_solic_usuario      FOREIGN KEY (id_usuario_solicitante) REFERENCES usuarios      (id_usuario) ON DELETE CASCADE,
            CONSTRAINT fk_solic_respondedor  FOREIGN KEY (respondido_por)         REFERENCES usuarios      (id_usuario) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)


def downgrade() -> None:
    for tabela in [
        "viagem_solicitacoes", "viagem_publicacao_comentarios",
        "viagem_publicacao_curtidas", "viagem_publicacoes",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {tabela}")
