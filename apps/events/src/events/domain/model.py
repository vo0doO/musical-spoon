from datetime import date

from pydantic import condecimal, field_serializer, field_validator
from sqlmodel import CheckConstraint, Field, Index, SQLModel


class EventBase(SQLModel):
    name: str = Field(description='Event name')
    description: str = Field(description='Event description')
    event_date: date = Field(description='Event date')
    available_tickets: int = Field(description='Number of available tickets', ge=0)
    ticket_price: condecimal(decimal_places=2) = Field(description='ticket price', gt=0)  # type: ignore
    deleted_at: date | None = Field(default=None, description='Date when the event was deleted')

    @field_validator('event_date')
    @classmethod
    def validate_event_date(cls, value: date) -> date:
        if value < date.today():
            raise ValueError('The date of the event cannot be the previous one')
        return value

    @field_serializer('ticket_price')
    def serialize_ticket_price(self, value: condecimal(decimal_places=2)):  # type: ignore
        return round(float(value), 2)


class Event(EventBase, table=True):
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={'autoincrement': True})

    __table_args__ = (
        CheckConstraint('available_tickets >= 0', name='check_available_tickets_non_negative'),
        CheckConstraint('ticket_price > 0', name='check_ticket_price_positive'),
        Index('idx_event_date', 'event_date', postgresql_using='btree'),
    )
