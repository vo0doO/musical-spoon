import pytest
from pydantic import ValidationError

from orders.domain.model import Order, OrderStatuses, Ticket

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('invalid_status', ['COMPLETE', 'UNCOMPLETE', 4, 5, 0])
def test_cant_create_order_if_status_not_in_order_statuses_enum(fake_order, invalid_status):
    bad_order_data = fake_order.model_dump()
    bad_order_data['order_status'] = invalid_status
    with pytest.raises(ValidationError, match='1 validation error for Order\norder_status'):
        Order.model_validate(bad_order_data)


@pytest.mark.parametrize('user_id', ['', 123, '123', '123ojda123das'])
def test_cannot_create_order_with_invalid_user_id(fake_order, user_id):
    bad_order_data = fake_order.model_dump()
    bad_order_data['user_id'] = user_id
    with pytest.raises((ValueError, ValidationError), match='Invalid ObjectId|Input should be a valid string'):
        Order.model_validate(bad_order_data)


@pytest.mark.parametrize(
    'ticket_data',
    [
        (),
        ({'event_id': 101, 'price': 120.00}, {'event_id': 103, 'price': 150.00}),
        ({'event_id': 101, 'price': 120.00},),
        ({'event_id': 11, 'price': 120.00},),
    ],
)
def test_can_add_or_delete_ticket_or_change_ticket_price_use_update_tickets(fake_order, ticket_data):
    ticket_data = [Ticket(**{**data, 'order_id': fake_order.id}) for data in ticket_data]
    fake_order.update_tickets(ticket_data)

    event_ids = {ticket.event_id for ticket in fake_order.tickets}
    prices = {ticket.event_id: ticket.price for ticket in fake_order.tickets}

    expected_event_ids = {dto.event_id for dto in ticket_data}

    assert event_ids == expected_event_ids

    for dto in ticket_data:
        assert prices[dto.event_id] == dto.price


@pytest.mark.parametrize(
    'event_ids',
    [
        [101],
        [101, 102],
        [101, 102, 999],
    ],
)
def test_can_refund_selected_tickets_only_when_order_is_done(fake_order, event_ids):
    fake_order.order_status = OrderStatuses.DONE
    fake_order.refund_tickets(event_ids)

    refunded_ids = {ticket.event_id for ticket in fake_order.tickets if ticket.refunded}
    expected_ids = set(event_ids).intersection({ticket.event_id for ticket in fake_order.tickets})

    assert refunded_ids == expected_ids


@pytest.mark.parametrize(
    'event_ids',
    [
        [101],
        [102],
    ],
)
def test_cant_refund_if_order_not_done(fake_order, event_ids):
    fake_order.refund_tickets(event_ids)

    for ticket in fake_order.tickets:
        assert ticket.refunded is False
