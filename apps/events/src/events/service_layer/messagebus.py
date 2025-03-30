import logging
from typing import Any

from events.adapters.eventpublisher import AbstractEventPublisher
from events.domain import commands, events
from events.service_layer.handlers import HANDLERS
from events.service_layer.unit_of_work import AbscractUnitOfWork

logger = logging.getLogger(__name__)

type Message = commands.Command | events.Event


class MessageBus:
    def __init__(self, uow: AbscractUnitOfWork, publish: AbstractEventPublisher):
        self.uow = uow
        self.publish = publish

    async def handle(self, message: Message) -> Any:
        result = None
        logger.debug(f'handling {type(message)} {message}')
        try:
            handler = HANDLERS[type(message)]
            result = await handler(message, uow=self.uow, publish=self.publish)
            return result
        except Exception as error:
            logger.exception(f'Exception handling {type(message)} {message}. {error}')
            raise error
