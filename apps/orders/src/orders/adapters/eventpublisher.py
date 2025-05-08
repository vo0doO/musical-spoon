from typing import Protocol

from orders.domain.events import Event


class AbstractEventPublisher(Protocol):
    async def send_event(self, event: Event) -> None: ...
