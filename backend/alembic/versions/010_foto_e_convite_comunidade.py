"""Foto de capa e código de convite da comunidade

Revision ID: 010
Revises: 009
Create Date: 2026-10-01

Duas adições pequenas em `comunidades`, no mesmo espírito do resto do app:

1. foto_capa — URL do Cloudinary, mesmo padrão de usuarios.foto_perfil.
2. codigo_convite — mesma ideia do código de convite de grupos_viagem
   (6 caracteres, gerado com secrets.choice), usado só quando a comunidade é
   privada: quem não tem o código não entra. É gerado sempre na criação
   (mesmo pra comunidade pública), pra já existir se o admin trocar a
   privacidade pra privada depois.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE comunidades
            ADD COLUMN foto_capa TEXT NULL AFTER descricao
    """)
    op.execute("""
        ALTER TABLE comunidades
            ADD COLUMN codigo_convite VARCHAR(10) NULL AFTER privacidade
    """)
    op.execute("""
        ALTER TABLE comunidades
            ADD UNIQUE KEY uq_comunidade_codigo_convite (codigo_convite)
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE comunidades DROP INDEX uq_comunidade_codigo_convite")
    op.execute("ALTER TABLE comunidades DROP COLUMN codigo_convite")
    op.execute("ALTER TABLE comunidades DROP COLUMN foto_capa")
