from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from auth.models import UserCreate, UserInDB
from auth.settings import MONGO_DATABASE, MONGO_URL, pwd_context


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


async def get_user(email: str, db: AsyncIOMotorDatabase) -> UserInDB | None:
    user_data = await db.users.find_one({'email': email})
    return UserInDB(**user_data) if user_data else None


async def create_user(data: UserCreate, db: AsyncIOMotorDatabase) -> UserInDB | None:
    existing_user = await db.users.find_one({'email': data.email})

    if existing_user:
        return None

    hashed_password = pwd_context.hash(data.password)
    user = UserInDB(email=data.email, username=data.username, hashed_password=hashed_password)

    await db.users.insert_one(user.model_dump())
    return user
