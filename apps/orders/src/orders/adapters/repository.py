from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from orders.domain.model import Order, OrderStatuses, Ticket


class AbstractRepository(Protocol):
    def add(self, order: Order) -> None: ...
    async def get_user_backet(self, user_id: str) -> Order | None: ...
    async def list_by_event_id(self, event_id: int) -> Sequence[Order] | None: ...


class SqlAlshemyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, order: Order) -> None:
        self.session.add(order)

    async def get(self, order_id: Order) -> Order | None:
        return await self.session.get(Order, order_id)

    async def delete(self, order: Order) -> None:
        if inspect(order).transient:  # type: ignore
            order = await self.get(order.id)  # type: ignore
        if order is not None:
            await self.session.delete(order)

    async def get_user_backet(self, user_id: str) -> Order | None:
        allowed_statuses = [OrderStatuses.CREATE, OrderStatuses.PAYMENT_PENDING]
        stmt = select(Order).where(Order.user_id == user_id, Order.order_status.in_(allowed_statuses))  # type: ignore
        result = await self.session.execute(stmt)
        return result.scalar()

    async def list_by_event_id(self, event_id: int) -> Sequence[Order] | None:
        stmt = select(Order).join(Ticket, isouter=False).where(Ticket.event_id == event_id)  # type: ignore
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()
