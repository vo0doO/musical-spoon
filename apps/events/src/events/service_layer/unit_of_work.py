from typing import AsyncContextManager, Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AbscractUnitOfWork(Protocol, AsyncContextManager):
    async def commit(self):
        raise NotImplementedError

    async def rollback(self):
        raise NotImplementedError


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def __aenter__(self) -> AbscractUnitOfWork:
        self.session = self.session_factory()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
