from fastapi import FastAPI

from .dependencies.db import init_database
from .routers import user

app = FastAPI(
    title='Events service.',
    description='A service to manage events and notify the order service about changes.',
    lifespan=init_database,
)

app.include_router(user.router)
