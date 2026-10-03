"""Verificação do email no cadastro.

Revision ID: 012
Revises: 011
"""
from typing import Sequence, Union

from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conexao = op.get_bind()
    existentes = {
        linha[0]
        for linha in conexao.exec_driver_sql("SHOW COLUMNS FROM usuarios").fetchall()
    }
    colunas = {
        "email_verificado": "TINYINT(1) NOT NULL DEFAULT 1",
        "codigo_verificacao_hash": "CHAR(64) NULL",
        "codigo_verificacao_expira": "DATETIME NULL",
        "tentativas_verificacao": "TINYINT UNSIGNED NOT NULL DEFAULT 0",
    }
    for nome, definicao in colunas.items():
        if nome not in existentes:
            op.execute(f"ALTER TABLE usuarios ADD COLUMN {nome} {definicao}")


def downgrade() -> None:
    op.execute("""
        ALTER TABLE usuarios
            DROP COLUMN tentativas_verificacao,
            DROP COLUMN codigo_verificacao_expira,
            DROP COLUMN codigo_verificacao_hash,
            DROP COLUMN email_verificado
    """)