from pydantic import BaseModel, Field, condecimal


class Event(BaseModel):
    pass

    model_config = {'frozen': True}


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
