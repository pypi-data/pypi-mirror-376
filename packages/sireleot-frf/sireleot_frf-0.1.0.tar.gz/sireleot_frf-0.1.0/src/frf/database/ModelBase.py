from _pydatetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.decl_api import DeclarativeMeta, registry

mapper_registry = registry(
    metadata=sa.MetaData(
        naming_convention={
            "column_names": lambda constraint, table: "__".join(
                [column.name for column in constraint.columns.values()]  # type: ignore
            ),
            "ix": "ix__%(table_name)s__%(column_names)s",
            "uq": "uq__%(table_name)s__%(column_names)s",
            "ck": "ck__%(table_name)s__%(constraint_name)s",
            "fk": "fk__%(table_name)s__%(column_names)s__%(referred_table_name)s",
            "pk": "pk__%(table_name)s",
        }
    )
)

class ModelBase(metaclass=DeclarativeMeta):
    __abstract__ = True
    registry = mapper_registry
    metadata = mapper_registry.metadata

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.id}"

    def __repr__(self):
        return self.__str__()


class ModelUpdateCreatedBase(ModelBase):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(sa.DateTime, server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime, onupdate=sa.func.now(), server_default=sa.func.now())
