from collections import Counter, defaultdict
from enum import Enum, auto
from typing import Annotated

from bson import ObjectId as _ObjectId
from pydantic import AfterValidator, BaseModel, condecimal, field_serializer
from sqlmodel import Field, Index, Relationship, SQLModel


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
        sa_relationship_kwargs={'lazy': 'joined'},
        passive_deletes='all',
    )

    __table_args__ = (Index('idx_order_user_id', 'user_id', postgresql_using='hash'),)

    def update_tickets(self, ticket_data: list['TicketUpdateDTO']) -> None:
        # Группируем текущие и новые билеты по event_id
        current_by_event = defaultdict(list)
        for ticket in self.tickets:
            current_by_event[ticket.event_id].append(ticket)

        new_counter = Counter(ticket.event_id for ticket in ticket_data)
        price_by_event = {dto.event_id: dto.price for dto in ticket_data}

        # Обрабатываем каждый event_id из нового списка
        for event_id, new_count in new_counter.items():
            existing_tickets = current_by_event.get(event_id, [])
            existing_count = len(existing_tickets)
            new_price = price_by_event.get(event_id, [])

            # Если билеты есть — проверим цену и количество
            if existing_count > new_count:
                # Удаляем лишние
                to_remove = existing_tickets[new_count:]
                for ticket in to_remove:
                    self.tickets.remove(ticket)

            elif existing_count < new_count:
                # Добавляем недостающие
                for _ in range(new_count - existing_count):
                    self.tickets.append(Ticket(event_id=event_id, price=new_price, order_id=self.id))

            # Обновляем цену, если отличается
            for ticket in self.tickets:
                if ticket.event_id == event_id and ticket.price != new_price:
                    ticket.price = new_price

        # Удаляем билеты, которых нет в новом списке вообще
        incoming_events_ids = set(new_counter.keys())
        self.tickets = [ticket for ticket in self.tickets if ticket.event_id in incoming_events_ids]

    def refund_tickets(self, refund_data: 'RefundDTO') -> None:
        if self.order_status not in (OrderStatuses.DONE, OrderStatuses.PAYMENT_PENDING):
            return

        for ticket in self.tickets:
            if ticket.event_id in refund_data.event_ids and not ticket.refunded:
                ticket.refund()

    @field_serializer('user_id')
    def serialize_user_id(self, value: ObjectId) -> str:
        return str(value)


class TicketUpdateDTO(BaseModel):
    model_config = {'frozen': True}

    event_id: int
    price: condecimal(decimal_places=2) = Field(gt=0)  # type: ignore


class RefundDTO(BaseModel):
    model_config = {'frozen': True}

    event_ids: list[int] = []
