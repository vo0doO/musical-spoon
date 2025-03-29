import pytest

from events.domain.model import Event
from events.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from tests.conftest import select_event_by_name

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_can_create_event(uow: SqlAlchemyUnitOfWork, fake_event: dict):
    async with uow:
        event = Event(**fake_event)
        uow.session.add(event)
        await uow.commit()

    event_name = fake_event['name']

    event = await select_event_by_name(uow, event_name)
    assert event is not None
    assert event['name'] == event_name


@pytest.mark.asyncio
async def test_rollback_uncommited_work_by_default(uow: SqlAlchemyUnitOfWork, fake_event: dict):
    async with uow:
        event = Event(**fake_event)
        uow.session.add(event)

    event = await select_event_by_name(uow, fake_event['name'])
    assert event is None


async def test_rollback_on_error(uow: SqlAlchemyUnitOfWork, fake_event: dict):
    with pytest.raises(ValueError, match='Simulated error'):  # noqa: PT012
        fake_event['ticket_price'] = -1
        async with uow:
            event = Event(**fake_event)
            uow.session.add(event)
            raise ValueError('Simulated error')
            await uow.session.commit()

    event = await select_event_by_name(uow, fake_event['name'])
    assert event is None
