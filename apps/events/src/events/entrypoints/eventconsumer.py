import asyncio
import json
from abc import ABC, abstractmethod

from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from events.adapters.eventpublisher import RabbitMQEventPublisher
from events.domain import events
from events.logger import logger
from events.service_layer.messagebus import MessageBus
from events.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from events.settings import POSTGRES_URL, RABBITMQ_URL


class AbstractEventConsumer(ABC):
    @abstractmethod
    def consume(self):
        raise NotImplementedError

    @abstractmethod
    async def on_message(self, message: AbstractIncomingMessage) -> None:
        raise NotImplementedError


class RabbitMQEventConsumer(AbstractEventConsumer):
    def __init__(self, bus: MessageBus, rabbitmq_url: str, queue_name: str = 'orders'):
        self.bus = bus
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name

    def deserialize_event(self, event_data: dict) -> events.Event | None:
        event_name = event_data.pop('name')
        event_class = getattr(events, event_name, None)

        if not event_class:
            logger.error(f'Unknown event type: {event_name}')
            return None

        return event_class(**event_data)  # type: ignore

    async def on_message(self, message: AbstractIncomingMessage) -> None:
        logger.info(f'Received message: {message.info()}. Body is {message.body!r}')

        body = message.body.decode()
        event_data = json.loads(body)
        event = self.deserialize_event(event_data)

        await self.bus.handle(event) if event else None

    async def consume(self):
        connection = await connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue('orders', durable=True)

            await queue.consume(self.on_message, no_ack=True)
            logger.info('Waiting for messages...')
            await asyncio.Future()


def create_engine(postgres_url: str) -> AsyncEngine:
    return create_async_engine(str(postgres_url), echo=False, future=True)


def create_uow(engine: AsyncEngine) -> SqlAlchemyUnitOfWork:
    session_factory = async_sessionmaker(engine)
    return SqlAlchemyUnitOfWork(session_factory)


def create_publisher(rabbitmq_url: str) -> RabbitMQEventPublisher:
    return RabbitMQEventPublisher(rabbitmq_url)


def create_messagebus(uow: SqlAlchemyUnitOfWork, publisher: RabbitMQEventPublisher) -> MessageBus:
    return MessageBus(uow, publisher)


async def main():
    engine = create_engine(POSTGRES_URL)
    uow = create_uow(engine)
    publisher = create_publisher(RABBITMQ_URL)
    bus = create_messagebus(uow, publisher)

    consumer = RabbitMQEventConsumer(bus, RABBITMQ_URL)
    await consumer.consume()


if __name__ == '__main__':
    asyncio.run(main())
