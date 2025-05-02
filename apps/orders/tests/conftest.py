from collections.abc import AsyncGenerator
from copy import deepcopy

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, text

from orders.adapters.repository import SqlAlshemyRepository
from orders.domain.model import Order, OrderStatuses, Ticket
from orders.service_layer.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture
def fake_order() -> Order:
    return Order(
        id=1,
        user_id='67f267cc870d069054169f05',
        tickets=[
            Ticket(event_id=101, order_id=1, price=100.00),
            Ticket(event_id=101, order_id=1, price=100.00),
            Ticket(event_id=102, order_id=1, price=200.00),
        ],
    )


@pytest.fixture
def fake_orders() -> list[Order]:
    statuses = list(OrderStatuses)

    return [
        Order(
            id=i + 1,
            user_id=f'67f267cc870d069054169f0{i + 1}',
            order_status=statuses[i],
            tickets=[
                Ticket(event_id=100 + 2 * i, order_id=i + 1, price=100.0 + i * 10),
                Ticket(event_id=100 + 2 * i, order_id=i + 1, price=110.0 + i * 10),
                Ticket(event_id=100 + 2 * i + 1, order_id=i + 1, price=120.0 + i * 10),
            ],
        )
        for i in range(3)
    ]


async def select_order_by_id(uow: SqlAlchemyUnitOfWork, order_id) -> Order | None:
    async with uow:
        order = await uow.orders.get(order_id)
        return deepcopy(order)


async def create_database(engine: AsyncEngine):
    if 'order' not in SQLModel.metadata.tables.keys():  # noqa: SIM118
        from orders.domain.model import Order, Ticket  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_database(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


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
async def sqlite_session(sqlite_session_factory: async_sessionmaker[AsyncSession]):
    async with sqlite_session_factory() as session:
        yield session


@pytest.fixture
async def sqlite_fake_orders(sqlite_session: AsyncSession, fake_orders: list[Order]) -> AsyncGenerator[Order]:
    orders = [order.model_copy() for order in fake_orders]

    sqlite_session.add_all(fake_orders)
    await sqlite_session.commit()

    yield orders

    await sqlite_session.execute(text('delete from "order"'))


@pytest.fixture
def sqlite_repository(sqlite_session: AsyncSession) -> SqlAlshemyRepository:
    return SqlAlshemyRepository(sqlite_session)


@pytest.fixture
def sqlite_uow(sqlite_session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(sqlite_session_factory)
