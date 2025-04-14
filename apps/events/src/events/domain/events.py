from pydantic import BaseModel, Field, condecimal, model_validator


class Event(BaseModel):
    model_config = {'frozen': True}
    name: str

    @model_validator(mode='before')
    def set_name(cls, data: dict) -> dict:
        if isinstance(data, dict):
            data['name'] = cls.__name__  # type: ignore
        return data


class TicketPriceChanged(Event):
    event_id: int
    new_price: condecimal(decimal_places=2) = Field(gt=0)  # type: ignore


class AvailableTicketsDecreased(Event):
    event_id: int
    remaining_tickets: int = Field(ge=0)


class TicketSold(Event):
    event_id: int


class Deleted(Event):
    event_id: int
