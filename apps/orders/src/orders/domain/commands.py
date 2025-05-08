from pydantic import BaseModel

from orders.domain.dtos import TicketDTO
from orders.domain.model import ObjectId


class Command(BaseModel):
    model_config = {'frozen': True}


class CreateBasket(Command):
    user_id: ObjectId


class UpdateBasket(Command):
    user_id: ObjectId
    tickets: list[TicketDTO]


class DeleteOrder(Command):
    order_id: int
    user_id: ObjectId
