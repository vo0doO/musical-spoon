from fastapi import HTTPException, status

CredentailsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Access Denied',
)

ForbiddenException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail='Access Denied',
)

EmailAlreadyExistsException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='This email is already registered. Please use a different email address or log in to your account.',
)
