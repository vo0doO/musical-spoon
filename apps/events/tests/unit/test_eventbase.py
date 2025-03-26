from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from events.domain.model import EventBase

pytestmark = pytest.mark.unit


def test_can_create_eventbase(data_for_fake_event):
    event = EventBase(**data_for_fake_event)

    assert event is not None

    assert event.name == data_for_fake_event['name']
    assert event.description == data_for_fake_event['description']
    assert event.event_date == data_for_fake_event['event_date']
    assert event.available_tikets == data_for_fake_event['available_tikets']
    assert float(event.ticket_price) == float(data_for_fake_event['ticket_price'])


@pytest.mark.parametrize(
    'yesterday_event_date', [datetime.today() - timedelta(days=1), datetime.today() - timedelta(days=2)]
)
def test_cant_create_an_eventbase_with_a_previous_event_date(data_for_fake_event, yesterday_event_date):
    data_for_fake_event['event_date'] = yesterday_event_date.date()

    with pytest.raises(ValidationError, match='The date of the event cannot be the previous one'):
        EventBase(**data_for_fake_event)


@pytest.mark.parametrize('bad_price', [8132.1123, 12141.123123123, 0, -1])
def test_cant_create_eventbase_with_bad_price_value(data_for_fake_event, bad_price):
    data_for_fake_event['ticket_price'] = bad_price

    with pytest.raises(
        ValidationError, match='Decimal input should have no more than 2 decimal places|Input should be greater than 0'
    ):
        EventBase(**data_for_fake_event)


@pytest.mark.parametrize('bad_available_tikets', [-2, 1.5])
def test_cant_create_eventbase_with_bad_available_tikets_value(data_for_fake_event, bad_available_tikets):
    data_for_fake_event['available_tikets'] = bad_available_tikets

    with pytest.raises(
        ValidationError, match='Input should be greater than or equal to 0|Input should be a valid integer'
    ):
        EventBase(**data_for_fake_event)
