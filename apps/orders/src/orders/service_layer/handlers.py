from collections.abc import Callable
from copy import deepcopy

from orders.domain import commands, events
from orders.domain.model import Order, Ticket
from orders.service_layer.unit_of_work import AbstractUnitOfWork


class OrderNotFoundError(Exception):
    pass


class OrderNotBelongUserError(Exception):
    pass


async def create_basket(cmd: commands.CreateBasket, uow: AbstractUnitOfWork) -> Order:
    async with uow:
        basket = await uow.orders.get_user_basket(**cmd.model_dump())

        if not basket:
            basket = Order(**cmd.model_dump())
            uow.orders.add(basket)
            await uow.commit()

        await uow.session.refresh(basket)

        return deepcopy(basket)


async def update_basket(cmd: commands.UpdateBasket, uow: AbstractUnitOfWork) -> Order:
    async with uow:
        basket = await uow.orders.get_user_basket(str(cmd.user_id))

        if not basket:
            msg = f'Basket not found for user: {cmd.user_id!s}'
            raise OrderNotFoundError(msg)

        tickets = [Ticket(event_id=ticket.event_id, price=ticket.price) for ticket in cmd.tickets]

        basket.update_tickets(tickets)
        await uow.commit()
        await uow.session.refresh(basket)

        return deepcopy(basket)


async def delete_order(cmd: commands.DeleteOrder, uow: AbstractUnitOfWork) -> None:
    async with uow:
        order = await uow.orders.get(cmd.order_id)

        if not order:
            msg = f'Order with id {cmd.order_id} not found'
            raise OrderNotFoundError(msg)

        if order.user_id != str(cmd.user_id):
            msg = f'Order {order.id} does not belong to this user: {cmd.user_id!s}'
            raise OrderNotBelongUserError(msg)

        await uow.orders.delete(order)
        await uow.commit()


HANDLERS: dict[type[commands.Command] | type[events.Event], Callable] = {
    commands.CreateBasket: create_basket,
    commands.DeleteOrder: delete_order,
    commands.UpdateBasket: update_basket,
}
