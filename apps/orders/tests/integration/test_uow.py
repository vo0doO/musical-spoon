import pytest

from orders.domain.model import Ticket
from tests.conftest import select_order_by_id

pytestmark = pytest.mark.integration


async def test_uow_can_add_order(sqlite_uow, fake_order):
    async with sqlite_uow:
        sqlite_uow.orders.add(fake_order)
        await sqlite_uow.commit()

    order = await select_order_by_id(sqlite_uow, fake_order.id)
    assert order == fake_order
    assert order is not fake_order


async def test_uow_can_retrive_a_order_and_update_tickets_to_it(sqlite_uow, sqlite_fake_orders):
    initial_order = sqlite_fake_orders[0].model_copy()

    async with sqlite_uow:
        order = await sqlite_uow.orders.get(initial_order.id)
        new_tickets = [Ticket(event_id=999, order_id=order.id, price=5000.00)]
        order.update_tickets(new_tickets)
        await sqlite_uow.commit()

    updated_order = await select_order_by_id(sqlite_uow, initial_order.id)
    assert updated_order.tickets != initial_order.tickets
    assert updated_order.tickets == new_tickets


async def test_rollback_uncommited_work_by_default(sqlite_uow, fake_order):
    async with sqlite_uow:
        sqlite_uow.orders.add(fake_order)

    fake_order = await select_order_by_id(sqlite_uow, fake_order.id)
    assert fake_order is None


async def test_rollback_on_error(sqlite_uow, fake_order):
    with pytest.raises(ValueError, match='Simulated error'):  # noqa: PT012
        async with sqlite_uow:
            sqlite_uow.session.add(fake_order)
            msg = 'Simulated error'
            raise ValueError(msg)
            await sqlite_uow.session.commit()

    fake_order = await select_order_by_id(sqlite_uow, fake_order.id)
    assert fake_order is None
