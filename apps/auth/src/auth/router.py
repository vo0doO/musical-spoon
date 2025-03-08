from typing import Annotated

from fastapi import APIRouter, Depends, Form, Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from auth.dependencies import (
    add_response_headers,
    authenticate_user,
    create_access_token,
    create_user,
    get_db,
    get_token_from_header,
    verify_token,
)
from auth.exceptions import CredentailsException, EmailAlreadyExistsException, ForbiddenException
from auth.models import Message, Token, UserCreate, UserInDB, UserLogin

router = APIRouter(tags=['Auth'])


@router.post('/signin')
async def signin(
    response: Response, form_data: Annotated[UserLogin, Form()], db: AsyncIOMotorDatabase = Depends(get_db)
) -> Token:
    user: UserInDB = await authenticate_user(form_data.email, form_data.password, db)  # type: ignore
    if not user:
        raise CredentailsException
    add_response_headers(response, user)
    return create_access_token({'sub': user.email, 'username': user.username})


@router.post('/signup')
async def signup(
    response: Response, form_data: Annotated[UserCreate, Form()], db: AsyncIOMotorDatabase = Depends(get_db)
) -> Token:
    user: UserInDB = await create_user(form_data, db)  # type: ignore
    if not user:
        raise EmailAlreadyExistsException
    add_response_headers(response, user)
    return create_access_token({'sub': user.email, 'username': user.username})


@router.post('/auth')
async def auth(
    response: Response,
    token: Annotated[str, Depends(get_token_from_header)],
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Message:
    user: UserInDB = await verify_token(token, db)  # type: ignore
    if not user:
        raise ForbiddenException
    add_response_headers(response, user)
    return Message(message='Authentication successful')


@router.post('/post')
async def list_users(db: AsyncIOMotorDatabase = Depends(get_db)) -> list[UserInDB]:
    return await db.users.find().to_list()
