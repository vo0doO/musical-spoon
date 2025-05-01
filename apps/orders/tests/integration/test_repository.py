import pytest
from sqlalchemy import select

from orders.domain.model import Order, Ticket

pytestmark = pytest.mark.integration


async def test_can_get_user_backet_if_backet_exist_and_has_valid_status(sqlite_repository, sqlite_fake_orders):
    order = await sqlite_repository.get_user_backet(sqlite_fake_orders[0].user_id)
    assert order == sqlite_fake_orders[0]


async def test_cant_get_user_backet_if_user_does_not_exist(sqlite_repository, sqlite_fake_orders):
    order = await sqlite_repository.get_user_backet(sqlite_fake_orders[0].user_id + 'ABC')
    assert order is None


async def test_cant_get_user_backet_if_user_order_exist_but_has_invalid_status(sqlite_repository, sqlite_fake_orders):
    invalid_order = sqlite_fake_orders[-1]

    order = await sqlite_repository.get_user_backet(invalid_order.user_id)
    assert order is None


async def test_can_get_order_list_if_exist_orders_with_tickets_to_this_event(sqlite_repository, sqlite_fake_orders):
    orders = await sqlite_repository.list_by_event_id(sqlite_fake_orders[1].tickets[0].event_id)
    assert orders == sqlite_fake_orders[1:2]


async def test_cant_get_order_list_if_does_not_exist_orders_with_tickets_to_this_event(
    sqlite_repository,
    sqlite_fake_orders,
):
    orders = await sqlite_repository.list_by_event_id(sqlite_fake_orders[0].tickets[0].event_id - 999)
    assert orders == []


async def test_can_get_multiple_orders_with_tickets_for_same_event(sqlite_repository, fake_orders):
    expected_orders = [order.model_copy() for order in fake_orders]

    new_event_id = 999

    for order in fake_orders:
        order.tickets.append(Ticket(event_id=new_event_id, price=100.00, order_id=order.id))
    sqlite_repository.session.add_all(fake_orders)

    orders = await sqlite_repository.list_by_event_id(new_event_id)
    assert orders == expected_orders


async def test_can_delete_order_if_order_exist(sqlite_repository, sqlite_fake_orders):
    order_to_delete = sqlite_fake_orders[0]
    await sqlite_repository.delete(order_to_delete)
    await sqlite_repository.session.commit()

    order = await sqlite_repository.get(order_to_delete.id)
    assert order is None


async def test_cant_delete_nonexistent_order(sqlite_repository, sqlite_fake_orders):
    order_to_delete = Order(id=999, user_id='67f267cc870d069054169f05')
    await sqlite_repository.delete(order_to_delete)

    orders = await sqlite_repository.session.execute(select(Order))
    orders = orders.unique().scalars().all()
    assert orders == sqlite_fake_orders
