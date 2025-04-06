from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from events.domain.commands import CreateEvent, UpdateEvent

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('bad_price', [8132.1123, 12141.123123123, 0, -1])
def test_cant_create_event_with_bad_price_value(fake_event, bad_price):
    fake_event['ticket_price'] = bad_price

    errors = r'Decimal input should have no more than 2 decimal places|Input should be greater than 0'
    with pytest.raises(ValidationError, match=errors):
        CreateEvent(**fake_event)


@pytest.mark.parametrize('bad_available_tickets', [-2, 1.5])
def test_cant_create_event_with_bad_available_tickets_value(fake_event, bad_available_tickets):
    fake_event['available_tickets'] = bad_available_tickets

    errors = r'Input should be greater than or equal to 0|Input should be a valid integer'
    with pytest.raises(ValidationError, match=errors):
        CreateEvent(**fake_event)


@pytest.mark.parametrize(
    'yesterday_event_datetime', [datetime.now() - timedelta(days=1), datetime.now() - timedelta(days=2)]
)
async def test_cant_create_event_with_a_previous_event_datetime(yesterday_event_datetime: datetime):
    with pytest.raises(ValidationError, match='The datetime of the event cannot be the previous one'):
        CreateEvent(id=1, event_datetime=yesterday_event_datetime)


@pytest.mark.parametrize(
    'yesterday_event_datetime', [datetime.now() - timedelta(days=1), datetime.now() - timedelta(days=2)]
)
async def test_cant_update_event_with_a_previous_event_datetime(yesterday_event_datetime: datetime):
    with pytest.raises(ValidationError, match='The datetime of the event cannot be the previous one'):
        UpdateEvent(id=1, event_datetime=yesterday_event_datetime)


@pytest.mark.parametrize('bad_price', [8132.1123, 12141.123123123, 0, -1])
def test_cant_update_event_with_bad_price_value(fake_event, bad_price):
    fake_event['ticket_price'] = bad_price

    errors = r'Decimal input should have no more than 2 decimal places|Input should be greater than 0'
    with pytest.raises(ValidationError, match=errors):
        UpdateEvent(id=1, **fake_event)


@pytest.mark.parametrize('bad_available_tickets', [-2, 1.5])
def test_cant_update_event_with_bad_available_tickets_value(fake_event, bad_available_tickets):
    fake_event['available_tickets'] = bad_available_tickets

    errors = r'Input should be greater than or equal to 0|Input should be a valid integer'
    with pytest.raises(ValidationError, match=errors):
        UpdateEvent(id=1, **fake_event)


def test_cant_update_event_without_all_fields():
    with pytest.raises(ValidationError, match='At least one field must be provided for update'):
        UpdateEvent(id=1)
