from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "ManPlan API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    JWT_ALGORITHM: str = "HS256"

    INITIAL_TENANT_NAME: str = "ManPlan Demo"
    INITIAL_TENANT_SLUG: str = "manplan-demo"
    INITIAL_ADMIN_NAME: str = "Administrador"
    INITIAL_ADMIN_EMAIL: str
    INITIAL_ADMIN_PASSWORD: str

    LOG_LEVEL: str = "INFO"


settings = Settings()  # type: ignore[call-arg]