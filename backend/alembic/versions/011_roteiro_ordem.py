"""Ordem dos itens de roteiro

Revision ID: 011
Revises: 010
Create Date: 2026-10-02

Adiciona `ordem` em `roteiros` para permitir mover itens para cima/baixo e
persistir a posição entre recarregamentos. Não existe uma coluna "dia"
estruturada (o "Dia N" que aparece em alguns títulos gerados por IA é texto
livre dentro de `titulo`, nunca foi um campo separado) — por isso o reordenar
usa a mesma coluna `ordem` para todos os itens da viagem, e o backend agrupa
por "dia" extraindo o número do próprio texto do título (ver
services/roteiro_service.py::_dia_de), sem precisar de uma nova coluna nem
alterar o conteúdo já salvo em `titulo`.

Backfill: cada roteiro já existente recebe a ordem que já tinha implicitamente
(ORDER BY data_criacao ASC), feito em Python por grupo para não depender de
window functions (compatível com versões mais antigas de MySQL).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE roteiros
            ADD COLUMN ordem INT NOT NULL DEFAULT 0
                AFTER origem_ia
    """)

    conexao = op.get_bind()
    grupos = conexao.exec_driver_sql(
        "SELECT DISTINCT id_grupo FROM roteiros"
    ).fetchall()
    for (id_grupo,) in grupos:
        itens = conexao.exec_driver_sql(
            "SELECT id_roteiro FROM roteiros WHERE id_grupo=%s "
            "ORDER BY data_criacao ASC, id_roteiro ASC",
            (id_grupo,),
        ).fetchall()
        for posicao, (id_roteiro,) in enumerate(itens):
            conexao.exec_driver_sql(
                "UPDATE roteiros SET ordem=%s WHERE id_roteiro=%s",
                (posicao, id_roteiro),
            )


def downgrade() -> None:
    op.execute("ALTER TABLE roteiros DROP COLUMN ordem")
