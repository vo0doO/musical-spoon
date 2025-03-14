import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from motor.core import AgnosticClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from testcontainers.mongodb import MongoDbContainer  # type: ignore

from auth.dependencies import get_db
from auth.main import app
from auth.models import UserCreate, UserInDB
from auth.settings import MONGO_DATABASE, pwd_context

AgnosticClient.get_io_loop = asyncio.get_running_loop  # type: ignore


@pytest.fixture(scope='session')
def mongo_container():
    with MongoDbContainer('mongo') as container:
        yield container


@pytest.fixture
async def mongo_db(mongo_container: MongoDbContainer) -> AsyncGenerator[AsyncIOMotorDatabase]:
    client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_container.get_connection_url())

    await client.drop_database(MONGO_DATABASE)

    mongo_db = client[MONGO_DATABASE]
    await mongo_db.users.create_index([('email', 1)], unique=True)
    yield mongo_db
    await client.drop_database(MONGO_DATABASE)

    client.close()


@pytest.fixture
def sample_user(mongo_db: AsyncIOMotorClient) -> UserCreate:
    user_create = UserCreate(email='user@example.com', username='string', password='string')

    return user_create


@pytest.fixture(autouse=True)
async def insert_user_in_mongo_db(mongo_db: AsyncIOMotorClient, sample_user: UserCreate) -> AsyncGenerator:
    user_in_db = UserInDB(
        email=sample_user.email, username=sample_user.username, hashed_password=pwd_context.hash(sample_user.password)
    )
    try:
        await mongo_db.users.drop()
        await mongo_db.users.insert_one(user_in_db.model_dump())
        yield
    finally:
        await mongo_db.users.drop()


@pytest.fixture
def api_client(mongo_db: AsyncIOMotorClient) -> Generator[TestClient]:
    async def db_override():
        return mongo_db

    app.dependency_overrides[get_db] = db_override

    api_client = TestClient(app)
    yield api_client

    app.dependency_overrides.clear()


def signin_user(api_client, email=None, password=None):
    data = {}

    if email is not None:
        data['email'] = email
    if password is not None:
        data['password'] = password

    return api_client.post('/signin', data=data)


def signup_user(api_client, email=None, password=None, username=None):
    data = {}

    if email is not None:
        data['email'] = email
    if password is not None:
        data['password'] = password
    if username is not None:
        data['username'] = username

    return api_client.post('/signup', data=data)


def authenticate_user(api_client, token=None):
    headers = {'Authorization': f'Bearer {token if token else ""}'}
    return api_client.post('/auth', headers=headers)


def assert_unprocessable_entity(response, field, error_type, error_message):
    assert response.status_code == 422

    detail = response.json()['detail'][0]
    assert detail['type'] == error_type
    assert detail['msg'] == error_message
    assert detail['loc'][1] == field
