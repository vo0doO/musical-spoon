from collections.abc import Callable
from datetime import datetime

from fastapi import Request, Response

from orders.logger import logger


async def log_requests(request: Request, call_next: Callable) -> Response:
    start_time = datetime.now()  # noqa: DTZ005

    log_data = {
        'method': request.method,
        'url': str(request.url),
        'headers': dict(request.headers),
        'query_params': dict(request.query_params),
        'body': await request.body(),
        'client': request.client.host if request.client else None,
    }

    try:
        response = await call_next(request)
        log_data['status_code'] = response.status_code
    except Exception as e:
        log_data['error'] = str(e)
        logger.error(log_data)
        raise

    end_time = datetime.now()  # noqa: DTZ005
    log_data['duration_ms'] = (end_time - start_time).total_seconds() * 1000  # type: ignore

    logger.info(log_data)

    return response
