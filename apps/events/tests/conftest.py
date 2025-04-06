from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import yarl
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, text
from testcontainers.postgres import PostgresContainer  # type: ignore

from events.adapters.eventpublisher import FakeEventPublisher
from events.domain.model import Event
from events.entrypoints.fastapi.main import app
from events.service_layer.messagebus import MessageBus
from events.service_layer.unit_of_work import SqlAlchemyUnitOfWork


async def create_database(engine):
    if 'event' not in SQLModel.metadata.tables.keys():
        from src.events.domain.model import Event  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_database(engine):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def select_event_by_name(uow: SqlAlchemyUnitOfWork, name):
    async with uow:
        result = await uow.session.execute(text('SELECT * FROM event WHERE name = :name'), dict(name=name))
        event = result.fetchone()
        return event._asdict() if event else event


@pytest.fixture
def fake_event() -> dict:
    return {
        'name': 'Fake Event',
        'description': 'Fake Event',
        'event_datetime': datetime.now() + timedelta(days=1),
        'available_tickets': 10,
        'ticket_price': 3000.15,
    }


@pytest.fixture(scope='session')
def postgres_container() -> Generator[PostgresContainer]:
    with PostgresContainer('postgres') as container:
        yield container


@pytest.fixture
async def postgres_engine(postgres_container: PostgresContainer) -> AsyncGenerator[AsyncEngine]:
    try:
        postgres_url = yarl.URL(postgres_container.get_connection_url()).with_scheme('postgresql+asyncpg')
        engine = create_async_engine(str(postgres_url), poolclass=NullPool)
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def postgres_session_factory(postgres_engine: AsyncEngine) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    await create_database(postgres_engine)
    yield async_sessionmaker(postgres_engine, expire_on_commit=False)
    await drop_database(postgres_engine)


@pytest.fixture
async def postgres_session(postgres_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
    async with postgres_session_factory() as session:
        yield session


@pytest.fixture
async def sqlite_engine() -> AsyncGenerator[AsyncEngine]:
    try:
        engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=False, future=True)
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def sqlite_session_factory(sqlite_engine: AsyncEngine) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    await create_database(sqlite_engine)
    yield async_sessionmaker(sqlite_engine, expire_on_commit=False)
    await drop_database(sqlite_engine)


@pytest.fixture
def uow(sqlite_session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyUnitOfWork:
    uow = SqlAlchemyUnitOfWork(sqlite_session_factory)
    return uow


@pytest.fixture
def bus(uow: SqlAlchemyUnitOfWork) -> MessageBus:
    publish = FakeEventPublisher()
    messagebus = MessageBus(uow, publish)
    return messagebus


@pytest.fixture
def fake_events():
    def event_factory(i):
        return {
            'name': f'Event {i}',
            'description': f'Description {i}',
            'event_datetime': datetime.now() + timedelta(days=i),
            'available_tickets': abs(1 * i),
            'ticket_price': (i * 100) + 0.1 * i if i >= 0 else Decimal(f'{abs((i * 100) + 0.1 * i):.2f}'),
        }

    EventWithTomorrowDateHaveZeroTickets = Event.model_validate(
        {
            'name': 'Event tomorrow without tickets',
            'description': 'Event tomorrow without tickets',
            'event_datetime': datetime.now() + timedelta(days=1),
            'available_tickets': 0,
            'ticket_price': 2999.99,
        }
    )

    fake_events = [*[Event(**event_factory(i)) for i in range(-2, 0)]]
    fake_events.append(EventWithTomorrowDateHaveZeroTickets)
    fake_events.extend([Event.model_validate(event_factory(i)) for i in range(1, 11)])

    return fake_events


@pytest.fixture
async def sqlite_fake_events(uow: SqlAlchemyUnitOfWork, fake_events: list[Event]) -> AsyncGenerator[Event]:
    async with uow as uow:
        uow.session.add_all(fake_events)
        await uow.commit()

    yield fake_events

    async with uow as uow:
        uow.session.add_all(fake_events)
        await uow.session.execute(text('DELETE FROM event'))
        await uow.session.commit()


@pytest.fixture
def pg_uow(postgres_session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyUnitOfWork:
    uow = SqlAlchemyUnitOfWork(postgres_session_factory)
    return uow


@pytest.fixture
def pg_bus(pg_uow: SqlAlchemyUnitOfWork) -> MessageBus:
    publish = FakeEventPublisher()
    messagebus = MessageBus(pg_uow, publish)
    return messagebus


@pytest.fixture
async def pg_fake_events(pg_uow: SqlAlchemyUnitOfWork, fake_events: list[Event]) -> AsyncGenerator[Event]:
    async with pg_uow as uow:
        uow.session.add_all(fake_events)
        await uow.commit()

    yield fake_events

    async with pg_uow as uow:
        uow.session.add_all(fake_events)
        await uow.session.execute(text('DELETE FROM event'))
        await uow.session.commit()


@pytest.fixture
async def api_client(pg_bus: MessageBus) -> AsyncGenerator[TestClient]:
    from events.entrypoints.fastapi.dependencies.bus import bus

    async def bus_override():
        return pg_bus

    app.dependency_overrides[bus] = bus_override

    api_client = TestClient(app, headers={'X-User-Role': 'admin'})
    yield api_client

    app.dependency_overrides.clear()
