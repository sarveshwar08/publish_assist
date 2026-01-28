import uuid
from abc import ABC
from typing import Any, Callable, Dict, Generic, Type, TypeVar
from uuid import UUID

import numpy as np
from loguru import logger
from pydantic import UUID4, BaseModel, Field
from qdrant_client.http import exceptions
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import CollectionInfo, PointStruct, Record

from publish_assist.application.networks.embeddings import EmbeddingModelSingleton
from publish_assist.domain.exceptions import ImproperlyConfigured
from publish_assist.domain.types import DataCategory
from publish_assist.infra.db.qdrant import get_qdrant_client

T = TypeVar("T", bound="VectorBaseDocument")

class VectorBaseDocument(BaseModel, Generic[T], ABC):
    id: UUID4 = Field(default_factory=uuid.uuid4)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return False

        return self.id == value.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def from_record(cls: Type[T], point: Record) -> T:
        _id = UUID(point.id, version=4)
        payload = point.payload or {}

        attributes = {
            "id": _id,
            **payload,
        }
        if cls._has_class_attribute("embedding"):
            attributes["embedding"] = point.vector or None

        return cls(**attributes)

    def to_point(self: T, **kwargs) -> PointStruct:
        exclude_unset = kwargs.pop("exclude_unset", False)
        by_alias = kwargs.pop("by_alias", True)

        payload = self.model_dump(exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)

        chunk_id = payload.pop("chunk_id", None)
        if not chunk_id:
            raise ValueError("EmbeddedChunk must have chunk_id to be indexed in Qdrant")

        embedding = payload.pop("embedding", None)
        if not embedding:
            raise ValueError("EmbeddedChunk must have embedding before indexing")

        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist() # converts to py list, since quadrnt needs json

        payload.pop("id") #remove mongo id

        return PointStruct(id=chunk_id, vector=embedding, payload=payload)

    def model_dump(self: T, **kwargs) -> dict:
        dict_ = super().model_dump(**kwargs)

        dict_ = self._uuid_to_str(dict_)

        return dict_

    def _uuid_to_str(self, item: Any) -> Any:
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, UUID):
                    item[key] = str(value)
                elif isinstance(value, list):
                    item[key] = [self._uuid_to_str(v) for v in value]
                elif isinstance(value, dict):
                    item[key] = {k: self._uuid_to_str(v) for k, v in value.items()}

        return item

    @classmethod
    def bulk_insert(cls: Type[T], documents: list["VectorBaseDocument"]) -> bool:
        try:
            cls._bulk_insert(documents)
        except exceptions.UnexpectedResponse:
            logger.info(
                f"Collection '{cls.get_collection_name()}' does not exist. Trying to create the collection and reinsert the documents."
            )

            cls.create_collection()

            try:
                cls._bulk_insert(documents)
            except exceptions.UnexpectedResponse:
                logger.error(f"Failed to insert documents in '{cls.get_collection_name()}'.")

                return False

        return True

    @classmethod
    def _bulk_insert(cls: Type[T], documents: list["VectorBaseDocument"]) -> None:
        connection = get_qdrant_client()
        points = []
        skipped = []

        for doc in documents:
            try:
                point = doc.to_point()
                points.append(point)
            except (ValueError, TypeError) as e:
                skipped.append((doc, str(e)))

        if not points:
            logger.error(
                f"No valid points to insert into '{cls.get_collection_name()}'. "
                f"Skipped {len(skipped)} documents."
            )
            return

        if skipped:
            logger.warning(
                f"Skipped {len(skipped)} invalid documents while inserting into "
                f"'{cls.get_collection_name()}'."
            )

        connection.upsert(collection_name=cls.get_collection_name(), points=points)

    @classmethod
    def bulk_find(cls: Type[T], limit: int = 10, **kwargs) -> tuple[list[T], UUID | None]:
        try:
            documents, next_offset = cls._bulk_find(limit=limit, **kwargs)
        except exceptions.UnexpectedResponse:
            logger.error(f"Failed to search documents in '{cls.get_collection_name()}'.")

            documents, next_offset = [], None

        return documents, next_offset

    @classmethod
    def _bulk_find(cls: Type[T], limit: int = 10, **kwargs) -> tuple[list[T], UUID | None]:
        connection = get_qdrant_client()
        collection_name = cls.get_collection_name()

        offset = kwargs.pop("offset", None)
        offset = str(offset) if offset else None

        records, next_offset = connection.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=kwargs.pop("with_payload", True),
            with_vectors=kwargs.pop("with_vectors", False),
            offset=offset,
            **kwargs,
        )
        documents = [cls.from_record(record) for record in records]
        if next_offset is not None:
            next_offset = UUID(next_offset, version=4)

        return documents, next_offset

    @classmethod
    def search(cls: Type[T], query_vector: list, limit: int = 10, **kwargs) -> list[T]:
        try:
            documents = cls._search(query=query_vector, limit=limit, **kwargs)
        except exceptions.UnexpectedResponse:
            logger.error(f"Failed to search documents in '{cls.get_collection_name()}'.")

            documents = []

        return documents

    @classmethod
    def _search(cls: Type[T], query_vector: list, limit: int = 10, **kwargs) -> list[T]:
        connection = get_qdrant_client()
        collection_name = cls.get_collection_name()
        records = connection.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            with_payload=kwargs.pop("with_payload", True),
            with_vectors=kwargs.pop("with_vectors", False),
            **kwargs,
        )
        documents = [cls.from_record(record) for record in records]

        return documents

    @classmethod
    def get_or_create_collection(cls: Type[T]) -> CollectionInfo:
        connection = get_qdrant_client()
        collection_name = cls.get_collection_name()

        try:
            return connection.get_collection(collection_name=collection_name)
        except exceptions.UnexpectedResponse:
            use_vector_index = cls.get_use_vector_index()

            collection_created = cls._create_collection(
                collection_name=collection_name, use_vector_index=use_vector_index
            )
            if collection_created is False:
                raise RuntimeError(f"Couldn't create collection {collection_name}") from None

            return connection.get_collection(collection_name=collection_name)

    @classmethod
    def create_collection(cls: Type[T]) -> bool:
        collection_name = cls.get_collection_name()
        use_vector_index = cls.get_use_vector_index()

        return cls._create_collection(collection_name=collection_name, use_vector_index=use_vector_index)

    @classmethod
    def _create_collection(cls, collection_name: str, use_vector_index: bool = True) -> bool:
        connection = get_qdrant_client()
        if use_vector_index is True:
            vectors_config = VectorParams(size=EmbeddingModelSingleton().embedding_size, distance=Distance.COSINE) # cosine similarity will be used on this collection is search is called
        else:
            vectors_config = {}

        return connection.create_collection(collection_name=collection_name, vectors_config=vectors_config)

    @classmethod
    def get_category(cls: Type[T]) -> DataCategory:
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "category"):
            raise ImproperlyConfigured(
                "The class should define a Config class with"
                "the 'category' property that reflects the collection's data category."
            )

        return cls.Config.category

    @classmethod
    def get_collection_name(cls: Type[T]) -> str:
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "name"):
            raise ImproperlyConfigured(
                "The class should define a Config class with" "the 'name' property that reflects the collection's name."
            )

        return cls.Config.name

    @classmethod
    def get_use_vector_index(cls: Type[T]) -> bool:
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "use_vector_index"):
            return True

        return cls.Config.use_vector_index

    @classmethod
    def group_by_class(
        cls: Type["VectorBaseDocument"], documents: list["VectorBaseDocument"]
    ) -> Dict["VectorBaseDocument", list["VectorBaseDocument"]]:
        return cls._group_by(documents, selector=lambda doc: doc.__class__)

    @classmethod
    def group_by_category(cls: Type[T], documents: list[T]) -> Dict[DataCategory, list[T]]:
        return cls._group_by(documents, selector=lambda doc: doc.get_category())

    @classmethod
    def _group_by(cls: Type[T], documents: list[T], selector: Callable[[T], Any]) -> Dict[Any, list[T]]:
        grouped = {}
        for doc in documents:
            key = selector(doc)

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(doc)

        return grouped

    @classmethod
    def collection_name_to_class(cls: Type["VectorBaseDocument"], collection_name: str) -> type["VectorBaseDocument"]:
        for subclass in cls.__subclasses__():
            try:
                if subclass.get_collection_name() == collection_name:
                    return subclass
            except ImproperlyConfigured:
                pass

            try:
                return subclass.collection_name_to_class(collection_name)
            except ValueError:
                continue

        raise ValueError(f"No subclass found for collection name: {collection_name}")

    @classmethod
    def _has_class_attribute(cls: Type[T], attribute_name: str) -> bool:
        if attribute_name in cls.__annotations__:
            return True

        for base in cls.__bases__:
            if hasattr(base, "_has_class_attribute") and base._has_class_attribute(attribute_name):
                return True

        return False
