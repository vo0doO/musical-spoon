from fastapi import FastAPI

from events.router import router

app = FastAPI(
    title='Events service.',
    description='A service to manage events and notify the Order service about changes.',
)


app.include_router(router)
