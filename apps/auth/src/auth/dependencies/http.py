from fastapi import Response, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.exceptions import CredentailsException
from auth.models import UserInDB

security = HTTPBearer()


async def get_token_from_header(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    if not credentials.scheme == 'Bearer':
        raise CredentailsException
    return credentials.credentials


def add_response_headers(response: Response, user: UserInDB) -> None:
    response.headers['X-User-Role'] = user.role
    response.headers['X-User-Id'] = str(user.id)
