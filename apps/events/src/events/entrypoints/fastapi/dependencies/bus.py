from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from events.adapters.eventpublisher import AbstractEventPublisher, RabbitMQEventPublisher
from events.service_layer.messagebus import MessageBus
from events.service_layer.unit_of_work import SqlAlchemyUnitOfWork

from ..settings import RABBITMQ_URL  # type: ignore
from .db import session_factory  # type: ignore


async def uow(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(session_factory)],
) -> SqlAlchemyUnitOfWork:
    uow = SqlAlchemyUnitOfWork(session_factory)
    return uow


def publish() -> RabbitMQEventPublisher:
    publish = RabbitMQEventPublisher(RABBITMQ_URL)
    return publish


async def bus(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(uow)], publish: Annotated[AbstractEventPublisher, Depends(publish)]
) -> MessageBus:
    bus = MessageBus(uow, publish)
    return bus
