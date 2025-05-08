from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from orders.entrypoints.fastapi.dependencies.db import init_database
from orders.entrypoints.fastapi.exceptions import order_not_belong_user_handler, order_not_found_handler
from orders.entrypoints.fastapi.middlewares import log_requests
from orders.entrypoints.fastapi.router import router
from orders.service_layer.handlers import OrderNotBelongUserError, OrderNotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:  # noqa: ARG001
    async with init_database():
        yield


app = FastAPI(
    title='Orders service.',
    description='A service to manage orders and notify the events service about changes.',
    lifespan=lifespan,
)

app.add_exception_handler(OrderNotFoundError, order_not_found_handler)  # type: ignore
app.add_exception_handler(OrderNotBelongUserError, order_not_belong_user_handler)  # type: ignore

app.middleware('http')(log_requests)

app.include_router(router)
