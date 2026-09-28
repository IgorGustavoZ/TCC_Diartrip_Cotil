"""Compartilhamento de viagens/roteiros no Feed + mini feed do grupo + Comunidades

Revision ID: 008
Revises: 007
Create Date: 2026-09-27
Última revisão: 2026-09-28

Reaproveita a tabela `posts` (com curtidas/comentários que ela já tem) como a
base ÚNICA de publicação, em vez de criar um sistema de publicação paralelo
para cada ideia nova:

1. posts.id_grupo — mini feed privado de cada viagem (só fotos e texto, sem
   vídeo). id_grupo NULL continua sendo o Feed global de sempre.
2. posts.id_comunidade — feed de uma comunidade (mutuamente exclusivo com
   id_grupo; a regra fica no service, não em CHECK).
3. posts.tipo + ref_id_grupo/ref_id_roteiro — "compartilhar uma viagem" ou
   "compartilhar um roteiro" também vira só um post, com uma REFERÊNCIA
   (FOREIGN KEY) ao conteúdo original — nunca uma cópia do título/descrição.
   Se o original for apagado, o ON DELETE CASCADE remove o post também (a
   referência deixou de fazer sentido).
4. comunidades / comunidade_membros — grupos temáticos (ex.: "Amantes do
   Japão"), que NÃO são viagens: mesmo molde de grupos_viagem/grupo_membros
   (cargo admin/membro), mas entidade própria, sem datas nem roteiro.

(Revisão 2026-09-28: a primeira versão desta migration tinha adicionado
`roteiros.compartilhado_explorar`, um flag com listagem própria em
`/explorar/roteiros`. Como a migration ainda não tinha sido aplicada em
nenhum banco real, essa parte foi corrigida aqui em vez de empilhar uma nova
migration só para desfazê-la — substituída pelo mecanismo único acima.)
"""
from typing import Sequence, Union
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE posts
            ADD COLUMN id_grupo INT NULL AFTER id_usuario
    """)
    op.execute("""
        ALTER TABLE posts
            ADD COLUMN id_comunidade INT NULL AFTER id_grupo
    """)
    op.execute("""
        ALTER TABLE posts
            ADD COLUMN tipo ENUM('texto','viagem','roteiro') NOT NULL DEFAULT 'texto'
                AFTER id_comunidade
    """)
    op.execute("""
        ALTER TABLE posts
            ADD COLUMN ref_id_grupo INT NULL AFTER tipo
    """)
    op.execute("""
        ALTER TABLE posts
            ADD COLUMN ref_id_roteiro INT NULL AFTER ref_id_grupo
    """)
    op.execute("ALTER TABLE posts ADD INDEX idx_posts_grupo (id_grupo)")
    op.execute("ALTER TABLE posts ADD INDEX idx_posts_comunidade (id_comunidade)")
    op.execute("ALTER TABLE posts ADD INDEX idx_posts_ref_grupo (ref_id_grupo)")
    op.execute("ALTER TABLE posts ADD INDEX idx_posts_ref_roteiro (ref_id_roteiro)")
    op.execute("""
        ALTER TABLE posts
            ADD CONSTRAINT fk_post_grupo FOREIGN KEY (id_grupo)
                REFERENCES grupos_viagem (id_grupo) ON DELETE CASCADE
    """)
    op.execute("""
        ALTER TABLE posts
            ADD CONSTRAINT fk_post_ref_grupo FOREIGN KEY (ref_id_grupo)
                REFERENCES grupos_viagem (id_grupo) ON DELETE CASCADE
    """)
    op.execute("""
        ALTER TABLE posts
            ADD CONSTRAINT fk_post_ref_roteiro FOREIGN KEY (ref_id_roteiro)
                REFERENCES roteiros (id_roteiro) ON DELETE CASCADE
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS comunidades (
            id_comunidade INT          NOT NULL AUTO_INCREMENT,
            nome          VARCHAR(150) NOT NULL,
            descricao     TEXT         NULL,
            categoria     VARCHAR(100) NULL,
            privacidade   ENUM('publica','privada') NOT NULL DEFAULT 'publica',
            criado_por    INT          NOT NULL,
            data_criacao  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_comunidade),
            FULLTEXT KEY ft_nome_comunidade (nome),
            KEY idx_comunidades_privacidade (privacidade),
            CONSTRAINT fk_com_criador FOREIGN KEY (criado_por)
                REFERENCES usuarios (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS comunidade_membros (
            id            INT NOT NULL AUTO_INCREMENT,
            id_comunidade INT NOT NULL,
            id_usuario    INT NOT NULL,
            cargo         ENUM('admin','membro') NOT NULL DEFAULT 'membro',
            data_entrada  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uq_comunidade_usuario (id_comunidade, id_usuario),
            CONSTRAINT fk_cm_comunidade FOREIGN KEY (id_comunidade)
                REFERENCES comunidades (id_comunidade) ON DELETE CASCADE,
            CONSTRAINT fk_cm_usuario FOREIGN KEY (id_usuario)
                REFERENCES usuarios (id_usuario) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    op.execute("""
        ALTER TABLE posts
            ADD CONSTRAINT fk_post_comunidade FOREIGN KEY (id_comunidade)
                REFERENCES comunidades (id_comunidade) ON DELETE CASCADE
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE posts DROP FOREIGN KEY fk_post_comunidade")
    op.execute("DROP TABLE IF EXISTS comunidade_membros")
    op.execute("DROP TABLE IF EXISTS comunidades")

    op.execute("ALTER TABLE posts DROP FOREIGN KEY fk_post_ref_roteiro")
    op.execute("ALTER TABLE posts DROP FOREIGN KEY fk_post_ref_grupo")
    op.execute("ALTER TABLE posts DROP FOREIGN KEY fk_post_grupo")
    op.execute("ALTER TABLE posts DROP INDEX idx_posts_ref_roteiro")
    op.execute("ALTER TABLE posts DROP INDEX idx_posts_ref_grupo")
    op.execute("ALTER TABLE posts DROP INDEX idx_posts_comunidade")
    op.execute("ALTER TABLE posts DROP INDEX idx_posts_grupo")
    op.execute("ALTER TABLE posts DROP COLUMN ref_id_roteiro")
    op.execute("ALTER TABLE posts DROP COLUMN ref_id_grupo")
    op.execute("ALTER TABLE posts DROP COLUMN tipo")
    op.execute("ALTER TABLE posts DROP COLUMN id_comunidade")
    op.execute("ALTER TABLE posts DROP COLUMN id_grupo")
