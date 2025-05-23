from datetime import datetime

from pydantic import BaseModel, Field, condecimal, field_validator, model_validator


class Command(BaseModel):
    model_config = {'frozen': True}


class CreateEvent(Command):
    name: str = Field(description='Event name')
    description: str = Field(description='Event description')
    event_datetime: datetime = Field(description='Event datetime')
    available_tickets: int = Field(description='Number of available tickets', ge=0)
    ticket_price: condecimal(decimal_places=2) = Field(description='ticket price', gt=0)  # type: ignore

    @field_validator('event_datetime')
    @classmethod
    def validate_event_datetime(cls, value: datetime) -> datetime:
        if value < datetime.now():
            raise ValueError('The datetime of the event cannot be the previous one')
        return value


class UpdateEventFields(BaseModel):
    name: str | None = Field(default=None, description='Event name')
    description: str | None = Field(default=None, description='Event description')
    event_datetime: datetime | None = Field(default=None, description='Event datetime')
    available_tickets: int | None = Field(default=None, description='Number of available tickets', ge=0)
    ticket_price: condecimal(decimal_places=2) | None = Field(default=None, description='ticket price', gt=0)  # type: ignore

    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_field(cls, data: dict) -> dict:
        if all(value is None for key, value in data.items() if key != 'id'):
            raise ValueError('At least one field must be provided for update')
        return data

    @field_validator('event_datetime')
    @classmethod
    def validate_event_datetime(cls, value: datetime) -> datetime:
        if not value:
            return value
        if value.tzinfo is not None:
            raise ValueError('The datetime of the event cannot be have timezone or seconds. Example: 2025-04-05T18:48')
        if value < datetime.now():
            raise ValueError('The datetime of the event cannot be the previous one')
        return value


class UpdateEvent(Command, UpdateEventFields):
    id: int = Field(description='Event id')


class DeleteEvent(Command):
    id: int = Field(description='Event id')
    deleted_at: datetime = Field(default_factory=datetime.now, description='datetime when the event was deleted')
