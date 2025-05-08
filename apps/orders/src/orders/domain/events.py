from pydantic import BaseModel


class Event(BaseModel):
    model_config = {'frozen': True}


class TicketsSold(Event):
    event_id: int
    tickets_count: int
    name: str = __qualname__
