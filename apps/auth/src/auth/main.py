from fastapi import FastAPI
from auth.middlewares import log_requests
from auth.router import router

app = FastAPI(
    title='Auth service.',
    description='A secure authentication service to verify user identity before granting access to the system.',
)

app.middleware('http')(log_requests)
app.include_router(router)
