import json

import pytest

pytestmark = pytest.mark.e2e


async def assert_event_published(queue_iter, expected_message):
    async for message in queue_iter:
        async with message.process():
            if expected_message['name'] in (message := message.body.decode()):
                break

    assert expected_message == json.loads(message)


async def test_published_the_deleted_event_if_delete_event(api_client, pg_fake_events, rabbitmq_events_queue_iter):
    event_to_delete_id = pg_fake_events[-1].id

    api_client.delete(f'/events/{event_to_delete_id}')

    expected_message = {'name': 'Deleted', 'event_id': event_to_delete_id}

    await assert_event_published(rabbitmq_events_queue_iter, expected_message)


async def test_published_the_ticket_price_changed_event_if_update_event_price(
    api_client, pg_fake_events, rabbitmq_events_queue_iter
):
    event_to_update = pg_fake_events[-1]
    update_data = {'ticket_price': str(event_to_update.ticket_price - 100)}

    api_client.put(f'/events/{event_to_update.id}', json=update_data)

    expected_message = {
        'name': 'TicketPriceChanged',
        'event_id': event_to_update.id,
        'new_price': update_data['ticket_price'],
    }

    await assert_event_published(rabbitmq_events_queue_iter, expected_message)


async def test_published_the_available_tickets_decreased_event_if_decrease_available_tickets(
    api_client, pg_fake_events, rabbitmq_events_queue_iter
):
    event_to_update = pg_fake_events[-1]
    update_data = {'available_tickets': event_to_update.available_tickets - 5}

    api_client.put(f'/events/{event_to_update.id}', json=update_data)

    expected_message = {
        'name': 'AvailableTicketsDecreased',
        'event_id': event_to_update.id,
        'remaining_tickets': update_data['available_tickets'],
    }

    await assert_event_published(rabbitmq_events_queue_iter, expected_message)
