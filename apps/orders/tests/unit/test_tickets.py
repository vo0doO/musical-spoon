import pytest

from orders.domain.model import Ticket

pytestmark = pytest.mark.unit


def test_can_refund_ticket() -> None:
    ticket = Ticket.model_validate({'id': 1, 'event_id': 1, 'order_id': 1, 'price': 100.00})

    assert not ticket.refunded

    ticket.refund()
    assert ticket.refunded


def test_cant_refund_ticket_twice():
    ticket = Ticket(id=1, event_id=222, order_id=1, price=50.00)
    ticket.refund()

    assert ticket.refunded is True

    ticket.refund()
    assert ticket.refunded is True


@pytest.mark.parametrize(('id', 'event_id', 'order_id', 'price'), [(1, 10, 100, 1000.10), (2, 20, 200, 2000.20)])
def test_ticket_serialization(id, event_id, order_id, price):
    ticket = Ticket(id=id, event_id=event_id, order_id=order_id, price=price)
    dumped = ticket.model_dump()

    assert dumped['price'] == price
    assert dumped['order_id'] == order_id
    assert dumped['event_id'] == event_id
