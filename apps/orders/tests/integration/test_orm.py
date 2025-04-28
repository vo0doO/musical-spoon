import pytest

from orders.domain.model import Order

pytestmark = pytest.mark.integration


async def test_orm_mapper_can_load_order_with_tickets(sqlite_session, sqlite_fake_orders):
    order = await sqlite_session.get_one(Order, sqlite_fake_orders[0].id)
    assert order == sqlite_fake_orders[0]
