from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

user_id_header = APIKeyHeader(name='X-User-Id')


async def user_id(user_id: str = Depends(user_id_header)) -> str:
    if not user_id:
        raise HTTPException(status_code=403, detail='You must have a user_id !')
    return user_id


get_user_id = Annotated[str, Depends(user_id)]
