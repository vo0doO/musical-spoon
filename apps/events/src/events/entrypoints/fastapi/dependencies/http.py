from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

user_role_header = APIKeyHeader(name='X-User-Role')


async def is_admin(user_role: str = Depends(user_role_header)) -> None:
    if user_role != 'admin':
        raise HTTPException(status_code=403, detail='You must have a admin role !')


async def is_user(user_role: str = Depends(user_role_header)) -> None:
    if user_role not in ['admin', 'user']:
        raise HTTPException(status_code=403, detail='You must have a valid user role !')
