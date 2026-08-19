"""Marca roteiros gerados por IA

Revision ID: 006
Revises: 005
Create Date: 2026-08-19

Adiciona um flag simples em `roteiros` para exibir o badge "✨ Criado por IA"
no frontend. Não altera a estrutura de criação/edição/exclusão — um roteiro
gerado por IA continua sendo um roteiro normal, editável e removível pelos
mesmos endpoints já existentes.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE roteiros
            ADD COLUMN origem_ia TINYINT(1) NOT NULL DEFAULT 0
                AFTER descricao
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE roteiros DROP COLUMN origem_ia")
