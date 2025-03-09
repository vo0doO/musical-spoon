from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError

from auth.models import Token
from auth.settings import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY


def create_token(data: dict) -> Token:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update(exp=expire)

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)

    return Token(access_token=encoded_jwt, token_type='bearer')


def decode_token(token: str) -> dict | InvalidTokenError:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
