from pydantic import BaseModel, Field, condecimal


class TicketDTO(BaseModel):
    model_config = {'frozen': True}

    event_id: int = Field(description='Event id')
    price: condecimal(decimal_places=2) = Field(gt=0, description='Ticket price')  # type: ignore
