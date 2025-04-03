from datetime import date

from sqlalchemy import select

from events.domain.model import Event
from events.service_layer.unit_of_work import AbstractUnitOfWork


async def event(uow: AbstractUnitOfWork, event_id: int) -> Event | None:
    async with uow:
        event = await uow.session.get(Event, event_id)
        return event.model_copy() if event else None


async def events(
    uow: AbstractUnitOfWork, date_from: date | None, date_to: date | None, page: int = 1, items_count: int = 20
) -> list[Event]:
    async with uow:
        query = select(Event).where(Event.available_tickets > 0)  # type: ignore

        if date_from:
            query = query.where(Event.event_date >= date_from)  # type: ignore
        if date_to:
            query = query.where(Event.event_date <= date_to)  # type: ignore

        offset = (page - 1) * items_count
        query = query.offset(offset).limit(items_count)

        result = await uow.session.execute(query)
        events = result.scalars().all()

        return [event.model_copy() for event in events]
