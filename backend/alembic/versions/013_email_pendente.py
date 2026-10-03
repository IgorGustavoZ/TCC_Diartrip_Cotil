"""Troca de email só vale depois de confirmar o código enviado ao novo endereço.

Revision ID: 013
Revises: 012
"""
from typing import Sequence, Union

from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conexao = op.get_bind()
    existentes = {
        linha[0]
        for linha in conexao.exec_driver_sql("SHOW COLUMNS FROM usuarios").fetchall()
    }
    if "email_pendente" not in existentes:
        op.execute("ALTER TABLE usuarios ADD COLUMN email_pendente VARCHAR(255) NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE usuarios DROP COLUMN email_pendente")
