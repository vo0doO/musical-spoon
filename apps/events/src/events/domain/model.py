from datetime import datetime

from pydantic import condecimal, field_serializer, field_validator
from sqlmodel import CheckConstraint, Field, Index, SQLModel


class EventBase(SQLModel):
    name: str = Field(description='Event name')
    description: str = Field(description='Event description')
    event_datetime: datetime = Field(description='Event datetime')
    available_tickets: int = Field(description='Number of available tickets', ge=0)
    ticket_price: condecimal(decimal_places=2) = Field(description='Ticket price', gt=0)  # type: ignore
    deleted_at: datetime | None = Field(default=None, description='Datetime when the event was deleted')

    @field_validator('event_datetime')
    @classmethod
    def validate_event_datetime(cls, value: datetime) -> datetime:
        if value < datetime.now():
            raise ValueError('The datetime of the event cannot be the previous one')
        return value

    @field_serializer('ticket_price')
    def serialize_ticket_price(self, value: condecimal(decimal_places=2)):  # type: ignore
        return round(float(value), 2)

    @field_serializer('event_datetime', 'deleted_at')
    def serialize_event_datetime(self, value: datetime):  # type: ignore
        if not value:
            return value
        return value.strftime('%Y-%m-%dT%H:%M')


class Event(EventBase, table=True):
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={'autoincrement': True})

    __table_args__ = (
        CheckConstraint('available_tickets >= 0', name='check_available_tickets_non_negative'),
        CheckConstraint('ticket_price > 0', name='check_ticket_price_positive'),
        Index('idx_event_datetime', 'event_datetime', postgresql_using='btree'),
    )
