from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from auth.dependencies.jwt import create_token
from tests.conftest import api_client, authenticate_user, sample_user, signin_user

pytestmark = pytest.mark.e2e


def test_user_can_authenticate(api_client, sample_user):
    signin_response = signin_user(api_client, email=sample_user.email, password=sample_user.password)
    token = signin_response.json()['access_token']

    response = authenticate_user(api_client, token)

    assert response.status_code == 200
    assert response.headers['X-User-Role'] == 'user'
    assert response.json() == {'message': 'Authentication successful'}


def test_user_cannot_authenticate_with_invalid_token(api_client):
    response = authenticate_user(api_client, 'invalid_token')

    assert response.status_code == 403
    assert 'Access Denied' in response.json()['detail']


def test_user_cannot_authenticate_without_token(api_client):
    response = authenticate_user(api_client)

    assert response.status_code == 403
    assert 'Not authenticated' in response.json()['detail']


def test_user_cannot_authenticate_with_nonexistent_user(api_client):
    token = create_token({'sub': 'nonexistent@example.com', 'username': 'nonexistent'})

    response = authenticate_user(api_client, token)

    assert response.status_code == 403
    assert 'Access Denied' in response.json()['detail']


def test_user_cannot_authenticate_with_expired_token(api_client, sample_user):
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=31)
    with patch('auth.dependencies.jwt.datetime') as mock_datetime:
        mock_datetime.now.return_value = expired_time
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        signin_response = signin_user(api_client, sample_user.email, sample_user.password)

    token = signin_response.json()['access_token']
    response = authenticate_user(api_client, token)

    assert response.status_code == 403
    assert 'Access Denied' in response.json()['detail']
