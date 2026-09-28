"""Mini feed privado do grupo (posts.id_grupo)

Revision ID: 008
Revises: 007
Create Date: 2026-09-27

Reaproveita a tabela `posts` (com curtidas/comentários que ela já tem) para
o mini feed privado de cada viagem — id_grupo NULL continua sendo o Feed
global de sempre; id_grupo preenchido vira o mini feed daquela viagem, só
visível aos membros dela.

IMPORTANTE: este arquivo reflete exatamente o que já foi EXECUTADO em
produção. Ele passou por uma reescrita neste repositório que nunca chegou a
rodar de novo no banco real (o Alembic rastreia só o ID da revisão, não o
conteúdo do arquivo — editar uma migration já aplicada não tem efeito
nenhum). Por isso o conteúdo foi revertido para bater com o schema real, e
tudo que veio depois (compartilhar viagem/roteiro no Feed, Comunidades) virou
a migration 009 — nunca edite uma migration já aplicada, sempre crie uma nova.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE roteiros
            ADD COLUMN compartilhado_explorar TINYINT(1) NOT NULL DEFAULT 0
                AFTER origem_ia
    """)
    op.execute("""
        ALTER TABLE roteiros
            ADD INDEX idx_roteiros_compartilhado (compartilhado_explorar)
    """)

    op.execute("""
        ALTER TABLE posts
            ADD COLUMN id_grupo INT NULL AFTER id_usuario
    """)
    op.execute("""
        ALTER TABLE posts
            ADD INDEX idx_posts_grupo (id_grupo)
    """)
    op.execute("""
        ALTER TABLE posts
            ADD CONSTRAINT fk_post_grupo FOREIGN KEY (id_grupo)
                REFERENCES grupos_viagem (id_grupo) ON DELETE CASCADE
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE posts DROP FOREIGN KEY fk_post_grupo")
    op.execute("ALTER TABLE posts DROP INDEX idx_posts_grupo")
    op.execute("ALTER TABLE posts DROP COLUMN id_grupo")
    op.execute("ALTER TABLE roteiros DROP INDEX idx_roteiros_compartilhado")
    op.execute("ALTER TABLE roteiros DROP COLUMN compartilhado_explorar")
