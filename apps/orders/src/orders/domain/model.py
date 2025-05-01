from enum import Enum, auto
from typing import Annotated

from bson import ObjectId as _ObjectId
from pydantic import AfterValidator, condecimal, field_serializer
from sqlmodel import CheckConstraint, Field, Index, Relationship, SQLModel


def check_object_id(value: str) -> _ObjectId:
    if not _ObjectId.is_valid(value):
        msg = 'Invalid ObjectId'
        raise ValueError(msg)
    return _ObjectId(value)


ObjectId = Annotated[str, AfterValidator(check_object_id)]


class OrderStatuses(Enum):
    CREATE = auto()
    PAYMENT_PENDING = auto()
    DONE = auto()


class Ticket(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={'autoincrement': True})
    event_id: int = Field()
    order_id: int = Field(foreign_key='order.id', ondelete='CASCADE')
    price: condecimal(decimal_places=2) = Field(gt=0)  # type: ignore
    refunded: bool = Field(default=False)
    order: 'Order' = Relationship(back_populates='tickets')

    __table_args__ = (
        CheckConstraint('price > 0', name='check_price_positive'),
        Index('idx_ticket_event_id', 'event_id', postgresql_using='hash'),
        Index('idx_ticker_order_id', 'order_id', postgresql_using='hash'),
    )

    def refund(self) -> None:
        self.refunded = True

    @field_serializer('price')
    def serialize_price(self, value: condecimal(decimal_places=2)) -> float:  # type: ignore
        return round(float(value), 2)


class Order(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={'autoincrement': True})
    order_status: OrderStatuses = Field(default=OrderStatuses.CREATE)
    user_id: ObjectId = Field()
    tickets: list[Ticket] = Relationship(
        back_populates='order',
        sa_relationship_kwargs={'lazy': 'joined', 'cascade': 'all, delete-orphan', 'single_parent': True},
    )

    __table_args__ = (Index('idx_order_user_id', 'user_id', postgresql_using='hash'),)

    def update_tickets(self, tickets: list[Ticket]) -> None:
        self.tickets = tickets

    def refund_tickets(self, event_ids: list[int]) -> None:
        if self.order_status not in (OrderStatuses.DONE, OrderStatuses.PAYMENT_PENDING):
            return

        for ticket in self.tickets:
            if ticket.event_id in event_ids and not ticket.refunded:
                ticket.refund()

    @field_serializer('user_id')
    def serialize_user_id(self, value: ObjectId) -> str:
        return str(value)
