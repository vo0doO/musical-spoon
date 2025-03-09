import os

from passlib.context import CryptContext

SECRET_KEY = os.environ['SECRET_KEY']
ALGORITHM = os.environ['ALGORITHM']
ACCESS_TOKEN_EXPIRE_MINUTES = float(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'auth_db')

MONGO_HOST = os.getenv('MONGO_HOST', 'auth_db')
MONGO_PORT = os.getenv('MONGO_PORT', '27017')
MONGO_USERNAME = os.environ['MONGO_INITDB_ROOT_USERNAME']
MONGO_PASSWORD = os.environ['MONGO_INITDB_ROOT_PASSWORD']

MONGO_URL = f'mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}'

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
