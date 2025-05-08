from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from orders.bootstrap import bootstrap
from orders.service_layer.messagebus import MessageBus
from orders.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from .db import session_factory  # type: ignore


async def uow(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(session_factory)],
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)


async def bus(uow: Annotated[SqlAlchemyUnitOfWork, Depends(uow)]) -> MessageBus:
    return bootstrap(uow)


get_bus = Annotated[MessageBus, Depends(bus)]
