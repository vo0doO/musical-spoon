from pydantic import BaseModel

from orders.domain.model import ObjectId, OrderStatuses


class TicketPublic(BaseModel):
    id: int
    event_id: int
    order_id: int
    price: float
    refunded: bool


class OrderPublic(BaseModel):
    id: int
    order_status: OrderStatuses
    user_id: ObjectId
    tickets: list[TicketPublic]
