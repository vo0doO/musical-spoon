from fastapi import FastAPI

from auth.router import router

app = FastAPI(
    title='Auth service.',
    description='A secure authentication service to verify user identity before granting access to the system.',
)


app.include_router(router)
