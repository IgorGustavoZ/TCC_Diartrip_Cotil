"""Orçamento individual na solicitação de participação

Revision ID: 005
Revises: 004
Create Date: 2026-08-17

Permite que quem solicita participação em uma viagem pública informe o
orçamento que pretende disponibilizar. O valor fica registrado na própria
solicitação (viagem_solicitacoes.orcamento) e, se aceito, é copiado para a
participação do usuário naquela viagem (grupo_membros.orcamento) — o
orçamento pertence à combinação usuário+viagem, não ao usuário isoladamente.
Ao aceitar, o valor também é somado a grupos_viagem.orcamento (orçamento
total da viagem).
"""
from typing import Sequence, Union
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE viagem_solicitacoes
            ADD COLUMN orcamento DECIMAL(12,2) NULL
                AFTER mensagem
    """)
    op.execute("""
        ALTER TABLE grupo_membros
            ADD COLUMN orcamento DECIMAL(12,2) NULL
                AFTER cargo
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE grupo_membros DROP COLUMN orcamento")
    op.execute("ALTER TABLE viagem_solicitacoes DROP COLUMN orcamento")
