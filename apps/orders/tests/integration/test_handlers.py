import pytest
from sqlalchemy import select

from orders.domain.commands import CreateBasket, DeleteOrder, UpdateBasket
from orders.domain.dtos import TicketDTO
from orders.domain.model import Order, OrderStatuses, Ticket
from orders.service_layer.handlers import OrderNotBelongUserError, OrderNotFoundError

pytestmark = pytest.mark.integration


class TestCreateBasket:
    async def test_create_basket_if_user_does_not_have_a_basket(self, sqlite_bus, fake_order):
        order = await sqlite_bus.handle(CreateBasket(user_id=fake_order.user_id))
        assert order.user_id == fake_order.user_id
        assert order.tickets == []

    async def test_retrive_basket_if_user_has_a_basket(self, sqlite_bus, sqlite_fake_orders):
        expected_order = sqlite_fake_orders[0].model_copy()

        order = await sqlite_bus.handle(CreateBasket(user_id=expected_order.user_id))
        assert order.tickets == expected_order.tickets
        assert order == expected_order


class TestUpdateBasket:
    async def test_can_update_basket(self, sqlite_bus, sqlite_fake_orders):
        expected_order = sqlite_fake_orders[0].model_copy()
        expected_order.tickets.pop(0)
        expected_order.tickets.append(Ticket(event_id=999, order_id=expected_order.id, price=5000.00))

        new_tickets = [TicketDTO(event_id=ticket.event_id, price=ticket.price) for ticket in expected_order.tickets]

        order = await sqlite_bus.handle(UpdateBasket(user_id=expected_order.user_id, tickets=new_tickets))
        assert order.tickets == expected_order.tickets
        assert order == expected_order

    async def test_cannot_update_basket_if_user_has_no_basket(self, sqlite_bus, fake_order):
        with pytest.raises(OrderNotFoundError, match=f'Basket not found for user: {fake_order.user_id}'):
            await sqlite_bus.handle(
                UpdateBasket(user_id=fake_order.user_id, tickets=[]),
            )


class TestDeleteOrder:
    async def test_can_delete_order_if_the_order_is_done_and_of_this_user(self, sqlite_bus, sqlite_fake_orders):
        expected_order = next((order for order in sqlite_fake_orders if order.order_status == OrderStatuses.DONE), None)

        await sqlite_bus.handle(DeleteOrder(order_id=expected_order.id, user_id=expected_order.user_id))

        orders = await sqlite_bus.uow.session.execute(select(Order))
        orders = orders.unique().scalars().all()

        assert expected_order not in orders

    async def test_cant_delete_nonexistent_order(self, sqlite_bus):
        non_existent_order_id = 9999
        user_id = '67f267cc870d069054169f05'

        with pytest.raises(OrderNotFoundError, match=f'Order with id {non_existent_order_id} not found'):
            await sqlite_bus.handle(DeleteOrder(order_id=non_existent_order_id, user_id=user_id))

    async def test_cant_delete_order_that_does_not_belong_to_user(self, sqlite_bus, sqlite_fake_orders):
        order = sqlite_fake_orders[0]
        wrong_user_id = order.user_id[:-2] + '99'

        with pytest.raises(
            OrderNotBelongUserError,
            match=f'Order {order.id} does not belong to this user: {wrong_user_id}',
        ):
            await sqlite_bus.handle(DeleteOrder(order_id=order.id, user_id=wrong_user_id))
