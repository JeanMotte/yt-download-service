from logging.config import fileConfig

from sqlalchemy import create_engine
from yt_download_service.app.utils.env import get_or_raise_env

from alembic import context

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

# Use base.metadata to autogenerate migration.
target_metadata = None

DB_NAME = get_or_raise_env("DB_NAME")
DB_HOST = get_or_raise_env("DB_HOST")
DB_PORT = get_or_raise_env("DB_PORT")
DB_USER = get_or_raise_env("DB_USER")
DB_PASS = get_or_raise_env("DB_PASS")
DB_URL = get_or_raise_env("DB_URL")

context.configure(
    url=DB_URL,
    target_metadata=target_metadata,
    dialect_opts={"paramstyle": "named"},
    compare_type=True,
)


def run_migrations() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(DB_URL)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


run_migrations()
