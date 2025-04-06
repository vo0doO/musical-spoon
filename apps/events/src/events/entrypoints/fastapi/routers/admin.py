from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status

from events.domain.commands import CreateEvent, DeleteEvent, UpdateEvent, UpdateEventFields
from events.domain.model import Event
from events.service_layer.handlers import InvalidId
from events.service_layer.messagebus import MessageBus

from ..dependencies.bus import bus
from ..dependencies.http import is_admin

router = APIRouter(tags=['Events'], prefix='/events', dependencies=[Depends(is_admin)])


@router.post('/')
async def create_event(bus: Annotated[MessageBus, Depends(bus)], cmd: CreateEvent) -> Event:
    return await bus.handle(cmd)


@router.delete('/{id}')
async def delete_event(bus: Annotated[MessageBus, Depends(bus)], id: Annotated[int, Path(title='Event id')]) -> None:
    try:
        await bus.handle(DeleteEvent(id=id))
    except InvalidId as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.args)


@router.put('/{id}')
async def update_event(
    bus: Annotated[MessageBus, Depends(bus)], id: Annotated[int, Path(title='Event id')], cmd: UpdateEventFields
) -> Event:
    try:
        return await bus.handle(UpdateEvent(id=id, **cmd.model_dump()))
    except InvalidId as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.args)
