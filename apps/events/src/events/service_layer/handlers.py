from collections.abc import Callable
from datetime import datetime

from events.adapters.eventpublisher import AbstractEventPublisher
from events.domain import commands, events, model
from events.service_layer.unit_of_work import AbstractUnitOfWork


class InvalidId(Exception):
    pass


async def create_event(
    cmd: commands.CreateEvent, uow: AbstractUnitOfWork, publish: AbstractEventPublisher
) -> model.Event:
    async with uow:
        event = model.Event(**cmd.model_dump())
        uow.session.add(event)
        await uow.commit()
        return event


async def update_event(
    cmd: commands.UpdateEvent, uow: AbstractUnitOfWork, publish: AbstractEventPublisher
) -> model.Event:
    async with uow:
        event = await uow.session.get(model.Event, cmd.id)
        if not event:
            raise InvalidId(f'Invalid id {cmd.id}')

        original_ticket_price = event.ticket_price
        original_available_tickets = event.available_tickets

        update_data = cmd.model_dump(exclude={'id'}, exclude_unset=True, exclude_none=True)
        for field, value in update_data.items():
            setattr(event, field, value)

        uow.session.add(event)

        if 'ticket_price' in update_data and event.ticket_price != original_ticket_price:
            await publish.send_event(events.TicketPriceChanged(event_id=event.id, new_price=event.ticket_price))  # type: ignore

        if 'available_tickets' in update_data and event.available_tickets < original_available_tickets:
            await publish.send_event(
                events.AvailableTicketsDecreased(event_id=event.id, remaining_tickets=event.available_tickets)  # type: ignore
            )

        await uow.commit()
        return event


async def delete_event(cmd: commands.DeleteEvent, uow: AbstractUnitOfWork, publish: AbstractEventPublisher) -> None:
    async with uow:
        event = await uow.session.get(model.Event, cmd.id)

        if not event or event.deleted_at is not None:
            raise InvalidId(f'Invalid id {cmd.id}')

        event.deleted_at = cmd.deleted_at
        uow.session.add(event)

        if event.event_datetime > datetime.now():
            await publish.send_event(events.Deleted(event_id=event.id))  # type: ignore

        await uow.commit()


async def sell_tickets(eve: events.TicketsSold, uow: AbstractUnitOfWork, publish: AbstractEventPublisher) -> None:
    async with uow:
        event = await uow.session.get(model.Event, eve.event_id)
        if not event:
            raise InvalidId(f'Invalid id {eve.event_id}')

        event.available_tickets = event.available_tickets - eve.tickets_count

        await publish.send_event(
            events.AvailableTicketsDecreased(event_id=event.id, remaining_tickets=event.available_tickets)  # type: ignore
        )

        await uow.commit()


HANDLERS: dict[type[commands.Command] | type[events.Event], Callable] = {
    commands.CreateEvent: create_event,
    commands.DeleteEvent: delete_event,
    commands.UpdateEvent: update_event,
    events.TicketsSold: sell_tickets,
}
