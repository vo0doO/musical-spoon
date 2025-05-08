import inspect
from collections.abc import Callable
from functools import partial

from orders.adapters.eventpublisher import AbstractEventPublisher
from orders.service_layer import handlers, messagebus, unit_of_work


def bootstrap(
    uow: unit_of_work.AbstractUnitOfWork,
    publish: AbstractEventPublisher | None = None,
) -> messagebus.MessageBus:
    dependencies = {'uow': uow, 'publish': publish}

    injected_handlers = {
        cmd_type: inject_dependencies(handler, dependencies) for cmd_type, handler in handlers.HANDLERS.items()
    }

    return messagebus.MessageBus(uow=uow, handlers=injected_handlers)


def inject_dependencies(handler: Callable, dependencies: dict) -> Callable:
    params = inspect.signature(handler).parameters
    deps = {name: dependency for name, dependency in dependencies.items() if name in params}
    return partial(handler, **deps)
