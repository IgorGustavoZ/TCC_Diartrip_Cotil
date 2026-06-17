"""
Alembic Environment — configurado para usar raw SQL (sem SQLAlchemy ORM).

Como usar:
  # Aplicar todas as migrations pendentes
  alembic upgrade head

  # Ver estado atual
  alembic current

  # Criar nova migration (arquivo manual — autogenerate requer modelos SA)
  alembic revision -m "descricao_da_mudanca"

  # Reverter uma migration
  alembic downgrade -1
"""
import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Constrói a URL de conexão a partir das variáveis de ambiente —
# nunca armazenadas em texto plano em alembic.ini ou no repositório.
def _build_url() -> str:
    user     = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host     = os.getenv("DB_HOST", "localhost")
    port     = os.getenv("DB_PORT", "3306")
    name     = os.getenv("DB_NAME", "cl204032")
    return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{name}"


def run_migrations_offline() -> None:
    """Gera SQL sem conectar ao banco (útil para auditoria ou deploy manual)."""
    url = _build_url()
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Conecta ao banco e executa as migrations diretamente."""
    engine = create_engine(
        _build_url(),
        poolclass=pool.NullPool,  # Alembic usa conexão única, não precisa de pool
    )
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
