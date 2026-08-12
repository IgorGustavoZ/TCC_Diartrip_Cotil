"""Explorar viagens (catálogo de viagens públicas)

Revision ID: 004
Revises: 003
Create Date: 2026-08-12

A viagem pública deixa de ser representada por uma "publicação" separada
(tabelas viagem_publicacoes / viagem_publicacao_curtidas /
viagem_publicacao_comentarios, criadas na migration 003) e passa a ser a
própria linha de grupos_viagem, marcada com um flag `publica` e um
`limite_participantes`. As 3 tabelas de publicação nunca chegaram a ser
usadas por nenhum cliente e são removidas aqui. viagem_solicitacoes
(também criada em 003) é mantida sem alterações — já tem exatamente os
campos necessários para o fluxo de solicitação/aceitação.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE grupos_viagem
            ADD COLUMN publica TINYINT(1) NOT NULL DEFAULT 0
                AFTER preferencias
    """)
    op.execute("""
        ALTER TABLE grupos_viagem
            ADD COLUMN limite_participantes INT NULL DEFAULT NULL
                AFTER publica
    """)
    op.execute("""
        ALTER TABLE grupos_viagem
            ADD INDEX idx_grupos_publica (publica)
    """)

    for tabela in [
        "viagem_publicacao_comentarios", "viagem_publicacao_curtidas", "viagem_publicacoes",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {tabela}")


def downgrade() -> None:
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

    op.execute("ALTER TABLE grupos_viagem DROP INDEX idx_grupos_publica")
    op.execute("ALTER TABLE grupos_viagem DROP COLUMN limite_participantes")
    op.execute("ALTER TABLE grupos_viagem DROP COLUMN publica")
