import pytest

from tests.conftest import api_client, assert_unprocessable_entity, authenticate_user, sample_user, signup_user

pytestmark = pytest.mark.e2e


def test_user_can_signup(api_client):
    response = signup_user(api_client, email='newuser@example.com', password='newpassword', username='newuser')
    token = response.json()

    assert response.status_code == 200
    assert response.headers['X-User-Role'] == 'user'
    assert token['token_type'] == 'bearer'
    assert token['access_token'] is not None

    auth_response = authenticate_user(api_client, token['access_token'])

    assert auth_response.status_code == 200
    assert auth_response.headers['X-User-Role'] == 'user'
    assert auth_response.json() == {'message': 'Authentication successful'}


def test_user_cannot_signup_with_existing_email(api_client, sample_user):
    response = signup_user(api_client, email=sample_user.email, password='newpassword', username='newuser')

    assert response.status_code == 400
    assert 'This email is already registered' in response.json()['detail']


def test_user_cannot_signup_without_email(api_client):
    response = signup_user(api_client, password='newpassword', username='newuser')

    assert_unprocessable_entity(response, 'email', 'missing', 'Field required')


def test_user_cannot_signup_without_password(api_client):
    response = signup_user(api_client, email='newuser@example.com', username='newuser')

    assert_unprocessable_entity(response, 'password', 'missing', 'Field required')


def test_user_cannot_signup_with_empty_email(api_client):
    response = signup_user(api_client, email='', password='newpassword', username='newuser')

    assert_unprocessable_entity(
        response, 'email', 'value_error', 'value is not a valid email address: An email address must have an @-sign.'
    )


def test_user_cannot_signup_with_invalid_email(api_client):
    response = signup_user(api_client, email='+79991234123', password='newpassword', username='newuser')

    assert_unprocessable_entity(
        response, 'email', 'value_error', 'value is not a valid email address: An email address must have an @-sign.'
    )
