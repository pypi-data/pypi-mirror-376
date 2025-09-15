from uuid import uuid4

from asyncpg import Connection as AsyncpgConnection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from testcontainers.postgres import PostgresContainer

from src.frf.settings import settings, Environment


class CustomisedAsyncpgConnection(AsyncpgConnection):
    def _get_unique_id(self, prefix: str) -> str:
        return f"__asyncpg_{prefix}_{uuid4()}__"

match settings.ENV:
    case Environment.TESTING:
        container = PostgresContainer("postgres:16")
        container.start()
        db_url = container.get_connection_url(driver="asyncpg")
    case _:
        db_url = settings.DATABASE_URL

engine: AsyncEngine = create_async_engine(
    db_url,
    connect_args={
        "connection_class": CustomisedAsyncpgConnection,
        "server_settings": {
            "application_name": settings.SERVICE_NAME,
            "jit": "off",
        },
    },
    poolclass=AsyncAdaptedQueuePool,
    echo=settings.ENV == Environment.DEVELOPMENT,
)

db_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
