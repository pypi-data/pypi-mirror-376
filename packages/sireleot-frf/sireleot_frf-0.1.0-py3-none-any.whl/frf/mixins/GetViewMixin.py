from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from src.frf import depends
from src.frf.mixins.FrfBase import FrfBase

import sqlalchemy as sa


class GetViewMixin(FrfBase):
    async def get_view(
            self,
            request: Request,
            lookup_value: str,
            session: AsyncSession = Depends(depends.async_db_session())
    ) -> Response:
        if not hasattr(self.model, self.lookup_field):
            raise AttributeError(f"No attribute {self.lookup_field} defined")

        stmt = sa.Select(self.model).where(**{self.lookup_field: lookup_value})
        result = await session.execute(stmt)
        response = result.scalar_one()
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND)