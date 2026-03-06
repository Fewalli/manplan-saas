import os
import subprocess
import pytest


@pytest.fixture(scope="session", autouse=True)
def _ensure_db_migrated():
    """
    Garante que as tabelas existam antes de qualquer teste.
    Evita: psycopg.errors.UndefinedTable: relation "tenants" does not exist
    """
    env = os.environ.copy()
    if "DATABASE_URL" not in env:
        raise RuntimeError("DATABASE_URL must be set for tests")

    # roda migrations dentro do container (alembic.ini já está em /app)
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)