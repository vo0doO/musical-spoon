import asyncio
import json
from abc import ABC, abstractmethod

from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage

from events.domain import events
from events.logger import logger
from events.service_layer.messagebus import MessageBus


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
