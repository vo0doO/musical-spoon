from fastapi import FastAPI

app = FastAPI(
    title='Orders service.',
    description='A service to manage orders and notify the events service about changes.',
)


@app.get('/')
def hello_orders() -> str:
    return 'Hello Orders'
