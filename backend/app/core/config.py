from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Evolve Soluciones API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # JWT
    SECRET_KEY: str = "cambiar-en-produccion-clave-segura-2024"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # PostgreSQL (Auth)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "evolve_auth"

    # MySQL Local (Tenant)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = ""

    # MySQL Remote
    REMOTE_DB_HOST: str = ""
    REMOTE_DB_PORT: int = 3306
    REMOTE_DB_USER: str = ""
    REMOTE_DB_PASSWORD: str = ""
    REMOTE_DB_NAME: str = ""

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017/"
    MONGO_DB_NAME: str = "consolidado_archivos"

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"
    GEMINI_TIMEOUT: int = 120

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
