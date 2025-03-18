from fastapi import APIRouter, Request

router = APIRouter(tags=['Events'])


@router.get('/hello')
async def hello(request: Request) -> dict:
    return {'message': 'Hello Events', 'headers': dict(request.headers)}
