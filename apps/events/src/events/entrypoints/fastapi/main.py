import asyncio

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from events.entrypoints import eventconsumer

from .dependencies.db import init_database
from .middlewares import log_requests
from .routers import admin, user


@asynccontextmanager
async def lifespan(app):
    async with init_database():
        asyncio.create_task(eventconsumer.main())
        yield


app = FastAPI(
    title='Events service.',
    description='A service to manage events and notify the order service about changes.',
    lifespan=lifespan,
)

app.middleware('http')(log_requests)

app.include_router(user.router)
app.include_router(admin.router)
