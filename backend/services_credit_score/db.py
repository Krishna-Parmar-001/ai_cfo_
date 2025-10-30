# credit_score_service/db.py
from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config

MONGO_URI: str = config("MONGO_URI")
DB_NAME: str = config("DB_NAME")

_client: AsyncIOMotorClient | None = None
db = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    return _client

def init_db():
    global db
    client = get_client()
    db = client[DB_NAME]
    return db
