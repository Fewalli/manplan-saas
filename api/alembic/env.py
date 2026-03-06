from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

from manplan_api.db import Base
from manplan_api import models  # noqa: F401  (importa models p/ metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    # Prioriza env var do container
    return os.getenv("DATABASE_URL")

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()