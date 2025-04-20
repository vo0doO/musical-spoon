from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractConnection

from events.domain import events


class AbstractEventPublisher(ABC):
    @abstractmethod
    async def send_event(self, event: events.Event) -> None:
        raise NotImplementedError


class FakeEventPublisher(AbstractEventPublisher):
    def __init__(self):
        self.messages = []

    async def send_event(self, event: events.Event) -> None:
        self.messages.append(event)


class RabbitMQEventPublisher(AbstractEventPublisher):
    def __init__(self, rmq_url: str, queue_name: str = 'events') -> None:
        self.rmq_url: str = rmq_url
        self.queue_name: str = queue_name

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[AbstractChannel]:
        connection: AbstractConnection = await aio_pika.connect_robust(self.rmq_url)

        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(self.queue_name, durable=True)
            yield channel

    async def send_event(self, event: events.Event) -> None:
        message_body: bytes = event.model_dump_json().encode('utf8')

        async with self.connect() as channel:
            await channel.default_exchange.publish(aio_pika.Message(body=message_body), routing_key=self.queue_name)  # type: ignore
