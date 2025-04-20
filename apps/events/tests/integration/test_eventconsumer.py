import asyncio

import aio_pika
import pytest
from _pytest.logging import LogCaptureFixture

from events.adapters.eventpublisher import RabbitMQEventPublisher
from events.domain import events, model
from events.entrypoints.eventconsumer import RabbitMQEventConsumer

pytestmark = pytest.mark.integration


async def test_available_tickets_decreased_when_tickets_sold_event_sent(
    event_consumer: RabbitMQEventConsumer,
    sqlite_fake_events: list[model.Event],
    rabbitmq_orders_event_publisher: RabbitMQEventPublisher,
):
    event_to_sell_tickets = sqlite_fake_events[-1]

    tickets_sold_event = events.TicketsSold(event_id=event_to_sell_tickets.id, tickets_count=3)
    await rabbitmq_orders_event_publisher.send_event(tickets_sold_event)

    await asyncio.sleep(1)

    async with event_consumer.bus.uow as uow:
        updated_event = await uow.session.get(model.Event, event_to_sell_tickets.id)
        assert updated_event.available_tickets == event_to_sell_tickets.available_tickets - 3


async def test_raises_invalid_id_error_when_tickets_sold_event_sent_with_unknown_event_id(
    caplog: LogCaptureFixture,
    event_consumer: RabbitMQEventConsumer,
    sqlite_fake_events: list[model.Event],
    rabbitmq_orders_event_publisher: RabbitMQEventPublisher,
):
    caplog.set_level('ERROR')

    unknown_event_id = sqlite_fake_events[-1].id + 9999
    tickets_count = 3

    tickets_sold_event = events.TicketsSold(event_id=unknown_event_id, tickets_count=tickets_count)
    await rabbitmq_orders_event_publisher.send_event(tickets_sold_event)

    await asyncio.sleep(1)

    expected_error = f"InvalidId('Invalid id {unknown_event_id}')"
    assert any(expected_error in msg for msg in caplog.messages)


@pytest.mark.parametrize(
    ('event_body', 'expected_error'),
    [
        (b'{"event_id": 1}', "KeyError('name')"),
        (b'{"name": "TicketsSold", "event_id": 1}', 'error for TicketsSold\ntickets_count\n  Field required'),
        (b'{"name": "TicketsSold", "tickets_count": 1}', 'error for TicketsSold\nevent_id\n  Field required'),
    ],
)
async def test_raises_error_when_raw_event_message_sent_without_required_fields(
    caplog: LogCaptureFixture,
    event_consumer: RabbitMQEventConsumer,
    rabbitmq_orders_event_publisher: RabbitMQEventPublisher,
    event_body: bytes,
    expected_error,
):
    caplog.set_level('ERROR')

    async with rabbitmq_orders_event_publisher.connect() as channel:
        await channel.default_exchange.publish(
            aio_pika.Message(body=event_body), routing_key=rabbitmq_orders_event_publisher.queue_name
        )

    await asyncio.sleep(1)

    assert any(expected_error in msg for msg in caplog.messages)
