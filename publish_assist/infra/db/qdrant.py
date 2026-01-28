from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from publish_assist.settings import settings


class QdrantDatabaseConnector:
    _instance: QdrantClient | None = None

    def __new__(cls, *args, **kwargs) -> QdrantClient:
        if cls._instance is None:
            try:
                if settings.USE_QDRANT_CLOUD:
                    cls._instance = QdrantClient(
                        url=settings.QDRANT_CLOUD_URL,
                        api_key=settings.QDRANT_APIKEY,
                    )

                    uri = settings.QDRANT_CLOUD_URL
                else:
                    cls._instance = QdrantClient(
                        host=settings.QDRANT_DATABASE_HOST,
                        port=settings.QDRANT_DATABASE_PORT,
                    )

                    uri = f"{settings.QDRANT_DATABASE_HOST}:{settings.QDRANT_DATABASE_PORT}"

                logger.info(f"Connection to Qdrant DB with URI successful: {uri}")
            except UnexpectedResponse:
                logger.exception(
                    "Couldn't connect to Qdrant.",
                    host=settings.QDRANT_DATABASE_HOST,
                    port=settings.QDRANT_DATABASE_PORT,
                    url=settings.QDRANT_CLOUD_URL,
                )

                raise

        return cls._instance


def get_qdrant_client() -> QdrantClient:
    try:
        connection = QdrantDatabaseConnector()
        return connection
    except Exception as e:
        logger.error(f"Failed to get Qdrant client: {e!s}")
        raise
        

