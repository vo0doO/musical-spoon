from abc import ABC, abstractmethod

from events.domain import events


class AbstractEventPublisher(ABC):
    @abstractmethod
    async def send_event(self, event: events.Event) -> None:
        raise NotImplementedError


class FakeEventPublisher(AbstractEventPublisher):
    def __init__(self):
        self.messages = []

    async def send_event(self, event: events.Event) -> None:
        self.messages.append(event)
