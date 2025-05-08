from typing import Annotated

from fastapi import APIRouter, Path

from orders.domain.commands import CreateBasket, DeleteOrder, UpdateBasket
from orders.domain.dtos import TicketDTO
from orders.entrypoints.fastapi.dependencies.bus import get_bus
from orders.entrypoints.fastapi.dependencies.http import get_user_id
from orders.entrypoints.fastapi.models import OrderPublic

router = APIRouter(tags=['Events'], prefix='/order')


@router.post('/')
async def create_basket(bus: get_bus, user_id: get_user_id) -> OrderPublic:
    return await bus.handle(CreateBasket(user_id=user_id))


@router.put('/')
async def update_basket(bus: get_bus, user_id: get_user_id, tickets: list[TicketDTO]) -> OrderPublic:
    return await bus.handle(UpdateBasket(user_id=user_id, tickets=tickets))


@router.delete('/{id}')
async def delete_order(bus: get_bus, user_id: get_user_id, id: Annotated[int, Path(title='Order id')]) -> None:
    return await bus.handle(DeleteOrder(user_id=user_id, order_id=id))
