import pytest

from tests.conftest import api_client, assert_unprocessable_entity, authenticate_user, sample_user, signin_user

pytestmark = pytest.mark.e2e


def test_user_can_signin(api_client, sample_user):
    response = signin_user(api_client, email=sample_user.email, password=sample_user.password)
    token = response.json()

    assert response.status_code == 200
    assert response.headers['X-User-Role'] == 'user'
    assert token['token_type'] == 'bearer'
    assert token['access_token'] is not None

    auth_response = authenticate_user(api_client, token['access_token'])

    assert auth_response.status_code == 200
    assert auth_response.headers['X-User-Role'] == 'user'
    assert auth_response.json() == {'message': 'Authentication successful'}


def test_user_cannot_signin_with_wrong_password(api_client, sample_user):
    response = signin_user(api_client, email=sample_user.email, password='wrongpassword')

    assert response.status_code == 401
    assert 'Access Denied' in response.json()['detail']


def test_user_cannot_signin_with_unknown_email(api_client):
    response = signin_user(api_client, email='unknown@example.com', password='unknownpassword')

    assert response.status_code == 401
    assert 'Access Denied' in response.json()['detail']


def test_user_cannot_signin_without_email(api_client):
    response = signin_user(api_client, password='string')

    assert_unprocessable_entity(response, 'email', 'missing', 'Field required')


def test_user_cannot_signin_without_password(api_client):
    response = signin_user(api_client, email='user@example.com')

    assert_unprocessable_entity(response, 'password', 'missing', 'Field required')


def test_user_cannot_signin_with_empty_email(api_client):
    response = signin_user(api_client, email='')

    assert_unprocessable_entity(
        response, 'email', 'value_error', 'value is not a valid email address: An email address must have an @-sign.'
    )


def test_user_cannot_signin_with_not_valid_email(api_client):
    response = signin_user(api_client, email='+79991234123')

    assert_unprocessable_entity(
        response, 'email', 'value_error', 'value is not a valid email address: An email address must have an @-sign.'
    )
