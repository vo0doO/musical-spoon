import datetime
from collections.abc import AsyncGenerator

import pytest
import yarl
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from testcontainers.postgres import PostgresContainer  # type: ignore


@pytest.fixture(scope='session')
def postgres_container():
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


async def create_database(postgres_engine):
    if 'event' not in SQLModel.metadata.tables.keys():
        from src.events.domain.model import Event  # noqa
    async with postgres_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_database(postgres_engine):
    async with postgres_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def setup_database(postgres_engine: AsyncEngine):
    await create_database(postgres_engine)
    yield
    await drop_database(postgres_engine)


@pytest.fixture
async def postgres_session_factory(postgres_engine: AsyncEngine, setup_database) -> async_sessionmaker[AsyncSession]:
    session_factory = async_sessionmaker(postgres_engine, expire_on_commit=False)
    return session_factory


@pytest.fixture
async def postgres_session(postgres_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
    async with postgres_session_factory() as session:
        yield session


@pytest.fixture
def data_for_fake_event() -> dict:
    return {
        'name': 'Fake Event',
        'description': 'Fake Event',
        'event_date': datetime.date.today(),
        'available_tikets': 10,
        'ticket_price': 1.15,
    }
