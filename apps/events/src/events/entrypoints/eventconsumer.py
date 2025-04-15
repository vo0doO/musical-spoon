import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from events.adapters.eventconsumer import RabbitMQEventConsumer
from events.adapters.eventpublisher import RabbitMQEventPublisher
from events.service_layer.messagebus import MessageBus
from events.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from events.settings import POSTGRES_URL, RABBITMQ_URL

engine = create_async_engine(str(POSTGRES_URL), echo=False, future=True)


def uow() -> SqlAlchemyUnitOfWork:
    session_factory = async_sessionmaker(engine)
    uow = SqlAlchemyUnitOfWork(session_factory)
    return uow


def publish() -> RabbitMQEventPublisher:
    publish = RabbitMQEventPublisher(RABBITMQ_URL)
    return publish


def messagebus(uow: SqlAlchemyUnitOfWork, publish: RabbitMQEventPublisher) -> MessageBus:
    return MessageBus(uow, publish)


async def main():
    bus = messagebus(uow=uow(), publish=publish())
    consumer = RabbitMQEventConsumer(bus, RABBITMQ_URL)
    await consumer.consume()


if __name__ == '__main__':
    asyncio.run(main())
