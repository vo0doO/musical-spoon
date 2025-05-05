from contextlib import AbstractAsyncContextManager
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from orders.adapters.repository import AbstractRepository, SqlAlshemyRepository


class AbstractUnitOfWork(Protocol, AbstractAsyncContextManager):
    session: AsyncSession
    orders: AbstractRepository

    async def commit(self) -> None:
        raise NotImplementedError

    async def rollback(self) -> None:
        raise NotImplementedError


class SqlAlchemyUnitOfWork:
    session: AsyncSession
    orders: AbstractRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def __aenter__(self) -> 'SqlAlchemyUnitOfWork':
        self.session = self.session_factory()
        self.orders = SqlAlshemyRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):  # noqa: ANN001, ANN204
        await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
