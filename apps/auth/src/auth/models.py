from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class UserRoles(str, Enum):
    user = 'user'
    admin = 'admin'


class UserBase(BaseModel):
    email: EmailStr
    username: str | None = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: lambda oid: str(oid)}


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    role: UserRoles = Field(default=UserRoles.user)


class UserInDB(UserRead):
    id: ObjectId | None = Field(default=None, alias='_id')
    hashed_password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Message(BaseModel):
    message: str
