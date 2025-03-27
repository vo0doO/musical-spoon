import datetime
from collections.abc import AsyncGenerator, Generator

import pytest
import yarl
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from testcontainers.postgres import PostgresContainer  # type: ignore

from events.service_layer.unit_of_work import SqlAlchemyUnitOfWork


async def create_database(engine):
    if 'event' not in SQLModel.metadata.tables.keys():
        from src.events.domain.model import Event  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_database(engine):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
def data_for_fake_event() -> dict:
    return {
        'name': 'Fake Event',
        'description': 'Fake Event',
        'event_date': datetime.date.today(),
        'available_tikets': 10,
        'ticket_price': 1.15,
    }


@pytest.fixture(scope='session')
def postgres_container() -> Generator[PostgresContainer]:
    with PostgresContainer('postgres') as container:
        yield container


@pytest.fixture
async def postgres_engine(postgres_container: PostgresContainer) -> AsyncGenerator[AsyncEngine]:
    try:
        postgres_url = yarl.URL(postgres_container.get_connection_url()).with_scheme('postgresql+asyncpg')
        engine = create_async_engine(str(postgres_url), echo=True, future=True)
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
        engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=True, future=True)
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def sqlite_session_factory(sqlite_engine: AsyncEngine) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    await create_database(sqlite_engine)
    yield async_sessionmaker(sqlite_engine, expire_on_commit=False)
    await drop_database(sqlite_engine)


@pytest.fixture
async def uow(sqlite_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[SqlAlchemyUnitOfWork]:
    uow = SqlAlchemyUnitOfWork(sqlite_session_factory)
    return uow
