from abc import ABC, abstractmethod
from typing import Generic, TypeVar, cast

from publish_assist.application.networks.embeddings import EmbeddingModelSingleton
from publish_assist.domain.chunks import ArticleChunk, Chunk, TranscriptChunk
from publish_assist.domain.embedded_chunks import (
    EmbeddedArticleChunk,
    EmbeddedChunk,
    EmbeddedTranscriptChunk,
)
from publish_assist.domain.queries import EmbeddedQuery, Query

ChunkT = TypeVar("ChunkT", bound=Chunk)
EmbeddedChunkT = TypeVar("EmbeddedChunkT", bound=EmbeddedChunk)

embedding_model = EmbeddingModelSingleton()


class EmbeddingDataHandler(ABC, Generic[ChunkT, EmbeddedChunkT]):

    def embed(self, data_model: ChunkT) -> EmbeddedChunkT:
        return self.embed_batch([data_model])[0]

    def embed_batch(self, data_model: list[ChunkT]) -> list[EmbeddedChunkT]:
        embedding_model_input = [data_model_value.content for data_model_value in data_model]
        embeddings = embedding_model.embed(embedding_model_input)

        embedded_chunk = [
            self.map_model(data_model, cast(list[float], embedding))
            for data_model, embedding in zip(data_model, embeddings, strict=False)
        ]

        return embedded_chunk

    @abstractmethod
    def map_model(self, data_model: ChunkT, embedding: list[float]) -> EmbeddedChunkT:
        pass


class QueryEmbeddingHandler(EmbeddingDataHandler):
    def map_model(self, data_model: Query, embedding: list[float]) -> EmbeddedQuery:
        return EmbeddedQuery(
            id=data_model.id,
            author_id=data_model.author_id,
            author_full_name=data_model.author_full_name,
            content=data_model.content,
            embedding=embedding,
            metadata={
                "embedding_model_id": embedding_model.model_id,
                "embedding_size": embedding_model.embedding_size,
                "max_input_length": embedding_model.max_input_length,
            },
        )


class TranscriptEmbeddingHandler(EmbeddingDataHandler):
    def map_model(self, data_model: TranscriptChunk, embedding: list[float]) -> EmbeddedTranscriptChunk:
        return EmbeddedTranscriptChunk(
            id=data_model.id,
            chunk_id=data_model.chunk_id,
            chunk_index=data_model.chunk_index,
            dataset_id=data_model.dataset_id,
            content=data_model.content,
            embedding=embedding,
            link=data_model.link,
            platform=data_model.platform,
            document_id=data_model.document_id,
            author_id=data_model.author_id,
            author_full_name=data_model.author_full_name,
            metadata={
                "embedding_model_id": embedding_model.model_id,
                "embedding_size": embedding_model.embedding_size,
                "max_input_length": embedding_model.max_input_length,
            },
        )


class ArticleEmbeddingHandler(EmbeddingDataHandler):
    def map_model(self, data_model: ArticleChunk, embedding: list[float]) -> EmbeddedArticleChunk:
        return EmbeddedArticleChunk(
            id=data_model.id,
            chunk_id=data_model.chunk_id,
            chunk_index=data_model.chunk_index,
            dataset_id=data_model.dataset_id,
            content=data_model.content,
            embedding=embedding,
            platform=data_model.platform,
            link=data_model.link,
            document_id=data_model.document_id,
            author_id=data_model.author_id,
            author_full_name=data_model.author_full_name,
            metadata={
                "embedding_model_id": embedding_model.model_id,
                "embedding_size": embedding_model.embedding_size,
                "max_input_length": embedding_model.max_input_length,
            },
        )