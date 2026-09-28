"""Compartilhamento de viagens/roteiros no Feed + Comunidades (aplicação real)

Revision ID: 009
Revises: 008
Create Date: 2026-09-29

A migration 008 já tinha sido EXECUTADA de verdade neste banco numa versão
anterior (só com `roteiros.compartilhado_explorar` e `posts.id_grupo`), antes
da correção de direção que reescreveu o arquivo 008 no repositório. Como o
Alembic rastreia apenas o ID da revisão (não o conteúdo do arquivo), editar
uma migration já aplicada não teve efeito nenhum no banco real — ele ficou
com o schema antigo, mesmo com `alembic current` reportando "008 (head)".

Esta migration 009 aplica, como um passo novo (nunca editando uma migration
já executada de novo), exatamente o que a versão corrigida do 008 deveria
ter aplicado:

1. Reverte `roteiros.compartilhado_explorar` — substituído pelo mecanismo
   de posts.tipo='roteiro' abaixo.
2. Adiciona a `posts`: `id_comunidade`, `tipo`, `ref_id_grupo`,
   `ref_id_roteiro` — a mesma tabela (com curtidas/comentários que já tem)
   vira a base única de publicação (Feed, mini feed do grupo e feed de
   comunidade), com referência ao conteúdo original, nunca cópia.
3. Cria `comunidades` / `comunidade_membros` — grupos temáticos, que NÃO são
   viagens (mesmo molde de grupos_viagem/grupo_membros, tabela própria).

`posts.id_grupo` e sua FK `fk_post_grupo` já existiam desde a execução real
do 008 antigo e não são tocados aqui.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE roteiros DROP INDEX idx_roteiros_compartilhado")
    op.execute("ALTER TABLE roteiros DROP COLUMN compartilhado_explorar")

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
    op.execute("ALTER TABLE posts ADD INDEX idx_posts_comunidade (id_comunidade)")
    op.execute("ALTER TABLE posts ADD INDEX idx_posts_ref_grupo (ref_id_grupo)")
    op.execute("ALTER TABLE posts ADD INDEX idx_posts_ref_roteiro (ref_id_roteiro)")
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
    op.execute("ALTER TABLE posts DROP INDEX idx_posts_ref_roteiro")
    op.execute("ALTER TABLE posts DROP INDEX idx_posts_ref_grupo")
    op.execute("ALTER TABLE posts DROP INDEX idx_posts_comunidade")
    op.execute("ALTER TABLE posts DROP COLUMN ref_id_roteiro")
    op.execute("ALTER TABLE posts DROP COLUMN ref_id_grupo")
    op.execute("ALTER TABLE posts DROP COLUMN tipo")
    op.execute("ALTER TABLE posts DROP COLUMN id_comunidade")

    op.execute("""
        ALTER TABLE roteiros
            ADD COLUMN compartilhado_explorar TINYINT(1) NOT NULL DEFAULT 0 AFTER origem_ia
    """)
    op.execute("ALTER TABLE roteiros ADD INDEX idx_roteiros_compartilhado (compartilhado_explorar)")
