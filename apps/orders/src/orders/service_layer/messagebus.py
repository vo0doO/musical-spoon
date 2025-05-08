from collections.abc import Callable
from typing import Any

from orders.domain import commands, events
from orders.logger import logger
from orders.service_layer.unit_of_work import AbstractUnitOfWork

type Message = commands.Command | events.Event


class MessageBus:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        handlers: dict[type[commands.Command] | type[events.Event], Callable],
    ) -> None:
        self.uow = uow
        self.handlers = handlers

    async def handle(self, message: Message) -> Any:  # noqa: ANN401
        logger.debug(f'handling {type(message).__name__} {message}')
        try:
            handler = self.handlers[type(message)]
            return await handler(message)
        except Exception as error:
            logger.exception(f'Exception handling {type(message).__name__} {message}. {error}')
            raise
