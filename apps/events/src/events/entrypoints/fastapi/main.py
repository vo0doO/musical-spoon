from fastapi import FastAPI

from .dependencies.db import init_database
from .middlewares import log_requests
from .routers import admin, user

app = FastAPI(
    title='Events service.',
    description='A service to manage events and notify the order service about changes.',
    lifespan=init_database,
)

app.middleware('http')(log_requests)

app.include_router(user.router)
app.include_router(admin.router)
