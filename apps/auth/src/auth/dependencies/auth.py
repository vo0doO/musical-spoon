from motor.motor_asyncio import AsyncIOMotorDatabase

from auth.models import UserInDB
from auth.settings import pwd_context

from .db import get_user
from .jwt import decode_token


async def auth_user(email: str, password: str, db: AsyncIOMotorDatabase) -> UserInDB | None:
    user = await get_user(email, db)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user


async def verify_token(token: str, db: AsyncIOMotorDatabase) -> UserInDB | None:
    payload = decode_token(token)
    if not payload:
        return None

    user = await get_user(payload.get('sub'), db)  # type: ignore
    return user
