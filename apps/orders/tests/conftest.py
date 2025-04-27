import pytest

from orders.domain.model import Order, Ticket


@pytest.fixture
def fake_order():
    return Order(
        id=1,
        user_id='67f267cc870d069054169f05',
        tickets=[
            Ticket(event_id=101, order_id=1, price=100.00),
            Ticket(event_id=102, order_id=1, price=200.00),
        ],
    )
