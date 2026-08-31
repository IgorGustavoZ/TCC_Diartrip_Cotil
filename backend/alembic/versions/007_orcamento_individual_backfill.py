"""Backfill de orçamento individual do criador

Revision ID: 007
Revises: 006
Create Date: 2026-08-20

O orçamento total da viagem passa a ser sempre a soma dos orçamentos
individuais em grupo_membros.orcamento (coluna já existente desde a
migration 005), nunca um campo único editado diretamente. Esta migration
não altera nenhum schema — é um backfill de DADO, uma única vez, para que
viagens já existentes não passem a mostrar orçamento total R$ 0,00 do dia
para a noite.

Para cada viagem, atribui ao CRIADOR o que sobra do orçamento antigo
(grupos_viagem.orcamento) depois de descontar quem já tem um orçamento
individual próprio (quem entrou via Explorar Viagens informando orçamento,
já tinha isso somado automaticamente no total antigo). Isso evita contar
esse valor duas vezes. Só afeta linhas onde o criador ainda está com
orcamento NULL — nunca sobrescreve um valor que a pessoa já tenha definido.

Downgrade: não há como distinguir com segurança, depois de rodado, "isso
foi preenchido por esta migration" de "isso já era NULL e continua NULL"
— por isso o downgrade só reverte para NULL as linhas que esta migration
teria preenchido (mesmo critério, aplicado ao inverso). É uma aproximação
segura, não uma reversão bit-a-bit garantida.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A subquery correlacionada original referenciava grupo_membros dentro
    # do UPDATE na própria grupo_membros — o MySQL proíbe isso ("can't
    # specify target table for update in FROM clause"), mesmo com um alias
    # diferente. Pré-computar a soma como uma tabela derivada separada
    # (JOIN) contorna a restrição, com o mesmo resultado.
    op.execute("""
        UPDATE grupo_membros gm
        JOIN grupos_viagem g
            ON gm.id_grupo = g.id_grupo AND gm.id_usuario = g.criado_por
        LEFT JOIN (
            SELECT gm2.id_grupo, SUM(gm2.orcamento) AS soma_outros
            FROM grupo_membros gm2
            JOIN grupos_viagem g2 ON g2.id_grupo = gm2.id_grupo
            WHERE gm2.id_usuario != g2.criado_por
            GROUP BY gm2.id_grupo
        ) outros ON outros.id_grupo = g.id_grupo
        SET gm.orcamento = GREATEST(
            COALESCE(g.orcamento, 0) - COALESCE(outros.soma_outros, 0),
            0
        )
        WHERE gm.orcamento IS NULL
          AND g.orcamento IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE grupos_viagem g
        JOIN grupo_membros gm
            ON gm.id_grupo = g.id_grupo AND gm.id_usuario = g.criado_por
        SET gm.orcamento = NULL
        WHERE g.orcamento IS NOT NULL
    """)
