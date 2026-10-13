"""Custos da viagem — opções de passagem/hospedagem pesquisadas via SerpApi

Revision ID: 014
Revises: 013

Nova tabela `opcoes_custo`: guarda só os campos curados de cada resultado que
o usuário decide salvar (nunca o dict bruto da SerpApi) e o estado dela no
fluxo salva -> orçamento -> paga/descartada. `id_gasto` referencia a MESMA
tabela `gastos` já usada pelo resto do sistema financeiro — "marcar como
paga" reaproveita gasto_service.criar(), nunca duplica a lógica de despesas.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS opcoes_custo (
            id_opcao INT AUTO_INCREMENT PRIMARY KEY,
            id_grupo INT NOT NULL,
            id_usuario INT NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'salva',
            nome VARCHAR(255) NOT NULL,
            origem VARCHAR(255) NULL,
            destino VARCHAR(255) NULL,
            data_ida DATE NULL,
            data_volta DATE NULL,
            preco DECIMAL(10,2) NOT NULL,
            moeda VARCHAR(10) NOT NULL DEFAULT 'BRL',
            link_externo VARCHAR(1000) NULL,
            detalhes JSON NULL,
            data_consulta DATETIME NOT NULL,
            id_gasto INT NULL,
            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_opcao_grupo FOREIGN KEY (id_grupo)
                REFERENCES grupos_viagem (id_grupo) ON DELETE CASCADE,
            CONSTRAINT fk_opcao_usuario FOREIGN KEY (id_usuario)
                REFERENCES usuarios (id_usuario) ON DELETE CASCADE,
            CONSTRAINT fk_opcao_gasto FOREIGN KEY (id_gasto)
                REFERENCES gastos (id_gasto) ON DELETE SET NULL,
            INDEX idx_opcoes_custo_grupo (id_grupo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS opcoes_custo")
