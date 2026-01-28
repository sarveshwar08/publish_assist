from loguru import logger
from pymongo import MongoClient, database
from pymongo.errors import ConnectionFailure

from publish_assist.settings import settings


class MongoDatabaseConnector:
    _instance: MongoClient | None = None

    def __new__(cls, *args, **kwargs) -> MongoClient:
        if cls._instance is None:
            try:
                cls._instance = MongoClient(settings.DATABASE_HOST)
            except ConnectionFailure as e:
                logger.error(f"Couldn't connect to the database: {e!s}")

                raise

        logger.info(f"Connection to MongoDB with URI successful: {settings.DATABASE_HOST}")

        return cls._instance


def get_mongo(db_name: str = settings.DATABASE_NAME) -> database.Database:
    try:
        client = MongoDatabaseConnector()
        logger.info(f"Connected to MongoDB database: {client[db_name]}")
        return client[db_name]
    except Exception as e:
        logger.error(f"Failed to get MongoDB database: {e!s}")
        raise


connection = MongoDatabaseConnector()
