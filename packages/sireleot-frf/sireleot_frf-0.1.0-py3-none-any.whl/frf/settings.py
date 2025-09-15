import os
from enum import StrEnum

from pydantic_settings import BaseSettings

class Environment(StrEnum):
    TESTING = "TESTING"
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"

class Settings(BaseSettings):
    SERVICE_NAME: str = "frf"
    ENV: Environment = Environment.DEVELOPMENT

    LISTEN_ADDRESS: str = '0.0.0.0'
    LISTEN_PORT: int = 8080

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/frf"

    class Config:
        case_sensitive = True
        env_file = os.environ.get("ENV_FILE_PATH", ".env")

settings = Settings()