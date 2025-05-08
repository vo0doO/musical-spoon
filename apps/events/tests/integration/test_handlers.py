import asyncio
from datetime import datetime, timedelta

import pytest

from events.domain import events, model
from events.domain.commands import CreateEvent, DeleteEvent, UpdateEvent
from events.service_layer.handlers import InvalidId
from events.service_layer.messagebus import MessageBus
from tests.conftest import select_event_by_name

pytestmark = pytest.mark.integration


class TestCreateEvent:
    async def test_can_create_event(self, bus: MessageBus, fake_event: dict):
        await bus.handle(CreateEvent(**fake_event))

        event = await select_event_by_name(bus.uow, name=fake_event['name'])

        assert event['name'] == fake_event['name']
        assert event['description'] == fake_event['description']
        assert event['ticket_price'] == fake_event['ticket_price']


class TestUpdateEvent:
    async def test_can_update_event(self, bus: MessageBus, fake_event: dict):
        event = await bus.handle(CreateEvent(**fake_event))

        update_data = {
            'id': event.id,
            'name': 'Updated name',
            'description': 'Updated description',
            'event_datetime': datetime.now() + timedelta(days=33),
            'available_tickets': 15,
            'ticket_price': 5000.00,
        }

        await bus.handle(UpdateEvent(**update_data))

        updated_event = await select_event_by_name(bus.uow, name=update_data['name'])
        assert updated_event['id'] == event.id
        assert updated_event['name'] == update_data['name']
        assert updated_event['description'] == update_data['description']
        assert updated_event['event_datetime'] == str(update_data['event_datetime'])
        assert updated_event['available_tickets'] == update_data['available_tickets']
        assert updated_event['ticket_price'] == update_data['ticket_price']

    async def test_ticket_price_chenged_event_sended_when_update_event_price(self, bus: MessageBus, fake_event: dict):
        event = await bus.handle(CreateEvent(**fake_event))

        new_price = event.ticket_price - 1000

        expected_event = events.TicketPriceChanged(event_id=event.id, new_price=new_price)

        await bus.handle(UpdateEvent(id=event.id, ticket_price=new_price))
        assert expected_event in bus.publish.messages

    async def test_available_tickets_decreased_event_sended_when_decrease_event_available_tickets(
        self, bus: MessageBus, fake_event: dict
    ):
        event = await bus.handle(CreateEvent(**fake_event))

        new_available_tickets = event.available_tickets - 5

        expected_event = events.AvailableTicketsDecreased(event_id=event.id, remaining_tickets=new_available_tickets)

        await bus.handle(UpdateEvent(id=event.id, available_tickets=new_available_tickets))
        assert expected_event in bus.publish.messages

    async def test_cant_update_non_existent_event(self, bus: MessageBus, fake_event: dict):
        with pytest.raises(InvalidId, match='Invalid id'):
            await bus.handle(UpdateEvent(id=1, name='Updated event'))


class TestDeleteEvent:
    async def test_can_delete_event(self, bus: MessageBus, fake_event: dict):
        event = await bus.handle(CreateEvent(**fake_event))

        await bus.handle(DeleteEvent(id=event.id))

        deleted_event = await select_event_by_name(bus.uow, fake_event['name'])

        assert datetime.fromisoformat(deleted_event['deleted_at']).strftime(
            '%Y-%m-%d %H:%M'
        ) == datetime.now().strftime('%Y-%m-%d %H:%M')

    async def test_delete_event_sended_when_delete_event(self, bus: MessageBus, fake_event: dict):
        event = await bus.handle(CreateEvent(**fake_event))

        expected_event = events.Deleted(event_id=event.id)

        await bus.handle(DeleteEvent(id=event.id))

        assert expected_event in bus.publish.messages

    async def test_cant_delete_non_existent_event(self, bus: MessageBus, fake_event: dict):
        with pytest.raises(InvalidId, match='Invalid id'):
            await bus.handle(DeleteEvent(id=1))

    async def test_delete_event_not_send_if_delete_past_event(self, bus: MessageBus, fake_event: dict):
        current_datetime = datetime.now() + timedelta(seconds=2)
        fake_event['event_datetime'] = current_datetime

        event = await bus.handle(CreateEvent(**fake_event))

        await asyncio.sleep(2)
        await bus.handle(DeleteEvent(id=event.id))

        unexpected_event = events.Deleted(event_id=event.id)
        assert unexpected_event not in bus.publish.messages


class TestSellTickets:
    async def test_can_sell_tickets(self, bus: MessageBus, sqlite_fake_events: list[model.Event]):
        event_to_sell_tickets = sqlite_fake_events[-1]

        await bus.handle(events.TicketsSold(event_id=event_to_sell_tickets.id, tickets_count=3))

        async with bus.uow as uow:
            updated_event = await uow.session.get(model.Event, event_to_sell_tickets.id)
            assert updated_event.available_tickets == event_to_sell_tickets.available_tickets - 3

    async def test_cant_sell_tickets_with_invalid_id(self, bus: MessageBus):
        invalid_event_id = 9999

        with pytest.raises(InvalidId, match=f'Invalid id {invalid_event_id}'):
            await bus.handle(events.TicketsSold(event_id=invalid_event_id, tickets_count=3))
