from datetime import datetime

from sqlalchemy import select

from events.domain.model import Event
from events.service_layer.unit_of_work import AbstractUnitOfWork


async def event(uow: AbstractUnitOfWork, event_id: int) -> Event | None:
    async with uow:
        event = await uow.session.get(Event, event_id)
        return event.model_copy() if event else None


async def events(
    uow: AbstractUnitOfWork,
    datetime_from: datetime | None,
    datetime_to: datetime | None,
    page: int = 1,
    items_count: int = 20,
) -> list[Event]:
    async with uow:
        query = select(Event).where(Event.available_tickets > 0)  # type: ignore

        if datetime_from:
            query = query.where(Event.event_datetime >= datetime_from)  # type: ignore
        if datetime_to:
            query = query.where(Event.event_datetime <= datetime_to)  # type: ignore

        offset = (page - 1) * items_count
        query = query.offset(offset).limit(items_count)

        result = await uow.session.execute(query)
        events = result.scalars().all()

        return [event.model_copy() for event in events]
