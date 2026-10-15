"""Login/cadastro com Google — identificador estável da conta Google

Revision ID: 015
Revises: 014

Adiciona `google_sub` (o campo `sub` do token de identidade do Google — um
identificador estável e único por conta Google, nunca o e-mail) em `usuarios`.
Nullable: contas tradicionais (email/senha) continuam com esse campo vazio.
UNIQUE: impede duas contas Diartrip vinculadas à mesma conta Google.

`senha_hash` continua NOT NULL (não alterado) — contas criadas via Google
recebem um hash aleatório que nenhuma senha real jamais vai bater, em vez de
afrouxar essa constraint pra um caso que o próprio código já contorna sem
precisar de uma migration adicional.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE usuarios
            ADD COLUMN google_sub VARCHAR(255) NULL UNIQUE AFTER senha_hash
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE usuarios DROP COLUMN google_sub")
