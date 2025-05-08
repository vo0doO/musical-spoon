from fastapi import Request
from fastapi.responses import JSONResponse

from orders.service_layer.handlers import OrderNotBelongUserError, OrderNotFoundError


async def order_not_found_handler(request: Request, exc: OrderNotFoundError) -> JSONResponse:  # noqa: ARG001
    return JSONResponse(status_code=404, content={'detail': str(exc)})


async def order_not_belong_user_handler(request: Request, exc: OrderNotBelongUserError) -> JSONResponse:  # noqa: ARG001
    return JSONResponse(status_code=403, content={'detail': str(exc)})
