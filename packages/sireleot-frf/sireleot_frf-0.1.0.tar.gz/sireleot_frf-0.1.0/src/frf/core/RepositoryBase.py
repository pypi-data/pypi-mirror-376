import abc

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.frf import depends
from src.frf.database.ModelBase import ModelBase
import sqlalchemy as sa


class RepositoryBase(abc.ABC):
    def __init__(self, model: ModelBase):
        self.model = model

    def get(self, id: int, session: AsyncSession = Depends(depends.async_db_session())) -> ModelBase:
        query = sa.select()
        session.execute()
