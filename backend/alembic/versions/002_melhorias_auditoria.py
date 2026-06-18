"""Melhorias identificadas na auditoria técnica

Revision ID: 002
Revises: 001
Create Date: 2026-06-16

Aplica todas as correções de banco de dados apontadas na auditoria:
  - Índice em seguidores(id_seguido): evita full table scan em listar_seguidores
  - Índice composto em chat_ia(id_usuario, id_grupo, data_interacao): otimiza histórico
  - Índice em posts(data_criacao): otimiza feed social ordenado por data
  - Adiciona data_criacao em grupos_viagem: timestamp de criação para ordenação/auditoria
  - Adiciona codigo_validade em grupos_viagem: suporte a expiração de convites
  - gastos.descricao VARCHAR(255) → VARCHAR(500): alinha com validador Pydantic
"""
from typing import Sequence, Union
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE seguidores
            ADD INDEX idx_seg_seguido (id_seguido)
    """)

    op.execute("ALTER TABLE chat_ia DROP INDEX idx_chatia_usuario")
    op.execute("ALTER TABLE chat_ia DROP INDEX idx_chatia_grupo")
    op.execute("""
        ALTER TABLE chat_ia
            ADD INDEX idx_chatia_usuario_grupo_data (id_usuario, id_grupo, data_interacao)
    """)

    op.execute("""
        ALTER TABLE posts
            ADD INDEX idx_posts_data (data_criacao DESC)
    """)

    op.execute("""
        ALTER TABLE grupos_viagem
            ADD COLUMN data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                AFTER criado_por
    """)

    op.execute("""
        ALTER TABLE grupos_viagem
            ADD COLUMN codigo_validade TIMESTAMP NULL DEFAULT NULL
                AFTER codigo_convite
    """)

    op.execute("""
        ALTER TABLE gastos
            MODIFY COLUMN descricao VARCHAR(500) NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE gastos MODIFY COLUMN descricao VARCHAR(255) NULL")
    op.execute("ALTER TABLE grupos_viagem DROP COLUMN codigo_validade")
    op.execute("ALTER TABLE grupos_viagem DROP COLUMN data_criacao")
    op.execute("ALTER TABLE posts DROP INDEX idx_posts_data")
    op.execute("ALTER TABLE chat_ia DROP INDEX idx_chatia_usuario_grupo_data")
    op.execute("ALTER TABLE chat_ia ADD INDEX idx_chatia_usuario (id_usuario)")
    op.execute("ALTER TABLE chat_ia ADD INDEX idx_chatia_grupo (id_grupo)")
    op.execute("ALTER TABLE seguidores DROP INDEX idx_seg_seguido")
