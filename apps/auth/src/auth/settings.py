import os

from passlib.context import CryptContext

SECRET_KEY = os.environ['SECRET_KEY']
ALGORITHM = os.environ['ALGORITHM']
ACCESS_TOKEN_EXPIRE_MINUTES = float(os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'])

MONGO_DATABASE = os.environ['MONGO_DATABASE']

MONGO_HOST = os.environ['MONGO_HOST']
MONGO_PORT = os.environ['MONGO_PORT']
MONGO_USERNAME = os.environ['MONGO_INITDB_ROOT_USERNAME']
MONGO_PASSWORD = os.environ['MONGO_INITDB_ROOT_PASSWORD']

MONGO_URL = f'mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}'

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
