from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from events.adapters.eventpublisher import FakeEventPublisher
from events.service_layer.messagebus import MessageBus
from events.service_layer.unit_of_work import SqlAlchemyUnitOfWork

from .db import session_factory


async def uow(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(session_factory)],
) -> SqlAlchemyUnitOfWork:
    uow = SqlAlchemyUnitOfWork(session_factory)
    return uow


async def bus(uow: Annotated[SqlAlchemyUnitOfWork, Depends(uow)]) -> MessageBus:
    bus = MessageBus(uow, FakeEventPublisher())
    return bus
