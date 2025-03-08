from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Response, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from auth.exceptions import CredentailsException
from auth.models import Token, UserCreate, UserInDB
from auth.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    MONGO_DATABASE,
    MONGO_URL,
    SECRET_KEY,
    pwd_context,
)

security = HTTPBearer()


async def get_token_from_header(credentails: HTTPAuthorizationCredentials = Security(security)) -> str | HTTPException:
    if not credentails.scheme == 'Bearer':
        raise CredentailsException
    return credentails.credentials


async def create_default_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index([('email', 1)], unique=True)


async def get_db() -> AsyncIOMotorDatabase:  # type: ignore
    client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URL)
    db = client[MONGO_DATABASE]
    await create_default_indexes(db)
    try:
        yield db
    finally:
        client.close()


def create_access_token(data: dict) -> Token:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update(exp=expire)

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)

    return Token(access_token=encoded_jwt, token_type='bearer')


async def get_user(email: str, db: AsyncIOMotorDatabase) -> UserInDB | None:
    user_data = await db.users.find_one({'email': email})
    return UserInDB(**user_data) if user_data else None


async def authenticate_user(email: str, password: str, db: AsyncIOMotorDatabase) -> UserInDB | None:
    user = await get_user(email, db)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user


async def verify_token(token: str, db: AsyncIOMotorDatabase) -> UserInDB | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return await get_user(payload.get('sub'), db)
    except InvalidTokenError:
        return None


async def create_user(data: UserCreate, db: AsyncIOMotorDatabase) -> UserInDB | None:
    existing_user = await db.users.find_one({'email': data.email})

    if existing_user:
        return None

    hashed_password = pwd_context.hash(data.password)
    user = UserInDB(email=data.email, username=data.username, hashed_password=hashed_password)

    await db.users.insert_one(user.dict())
    return user


def add_response_headers(response: Response, user: UserInDB) -> None:
    response.headers['X-User-Role'] = user.role
