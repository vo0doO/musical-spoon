import pytest
from sqlalchemy import select

from orders.domain.model import Order, Ticket

pytestmark = pytest.mark.integration


async def test_orm_mapper_can_load_order_with_tickets(sqlite_session, sqlite_fake_orders):
    order = await sqlite_session.get_one(Order, sqlite_fake_orders[0].id)
    assert order == sqlite_fake_orders[0]


async def test_orm_mapper_can_cascade_delete_orphan_tickets(sqlite_session, sqlite_fake_orders):  # noqa: ARG001
    orders = await sqlite_session.execute(select(Order))
    orders = orders.unique().scalars().all()

    for order in orders:
        order.tickets = []
    await sqlite_session.commit()

    tickets = await sqlite_session.execute(select(Ticket))
    tickets = tickets.unique().scalars().all()
    assert len(tickets) == 0
