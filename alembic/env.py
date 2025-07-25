from logging.config import fileConfig

from sqlalchemy import create_engine
from yt_download_service.app.utils.env import get_or_raise_env
from yt_download_service.infrastructure.database.models import Base

from alembic import context

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

# Import database models so that Alembic can detect them
#  And infere schema inside autogenerate
target_metadata = Base.metadata

DB_NAME = get_or_raise_env("DB_NAME")
DB_HOST = get_or_raise_env("DB_HOST")
DB_PORT = get_or_raise_env("DB_PORT")
DB_USER = get_or_raise_env("DB_USER")
DB_PASS = get_or_raise_env("DB_PASS")
DB_URL = get_or_raise_env("DB_URL")


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(DB_URL)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    pass
else:
    run_migrations_online()
