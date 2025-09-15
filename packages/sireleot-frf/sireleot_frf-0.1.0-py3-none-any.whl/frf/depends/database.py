from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.frf.database.db_engine import db_session_maker


@asynccontextmanager
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with db_session_maker() as session:
        async with session.begin():
            try:
                yield session
            except Exception as e:
                session.rollback()
                logger.exception(f"Rolling back transaction (due exception={e})")
                raise e