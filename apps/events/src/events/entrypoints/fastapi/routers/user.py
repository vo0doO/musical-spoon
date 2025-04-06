from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from events import views
from events.domain.model import Event
from events.service_layer.messagebus import MessageBus

from ..dependencies.bus import bus
from ..dependencies.http import is_user
from ..queries import EventsQuery

router = APIRouter(tags=['Events'], prefix='/events', dependencies=[Depends(is_user)])


@router.get('/{id}')
async def get_event(bus: Annotated[MessageBus, Depends(bus)], id: Annotated[int, Path(title='Event id')]) -> Event:
    event = await views.event(bus.uow, id)

    if not event:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    return event


@router.get('/')
async def get_events(bus: Annotated[MessageBus, Depends(bus)], query: Annotated[EventsQuery, Query()]) -> list[Event]:
    events = await views.events(
        uow=bus.uow,
        datetime_from=query.datetime_from,
        datetime_to=query.datetime_to,
        page=query.page,
        items_count=query.items_count,
    )

    if not events:
        raise HTTPException(status_code=404, detail='No events found')

    return events
