import hashlib
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from publish_assist.domain.chunks import ArticleChunk, Chunk, TranscriptChunk
from publish_assist.domain.cleaned_documents import (
    CleanedDocument,
    CleanedArticleDocument,
    CleanedTranscriptDocument,
)

from .operations import chunk_article, chunk_text

CleanedDocumentT = TypeVar("CleanedDocumentT", bound=CleanedDocument)
ChunkT = TypeVar("ChunkT", bound=Chunk)


class ChunkingDataHandler(ABC, Generic[CleanedDocumentT, ChunkT]):
    @property
    def metadata(self) -> dict:
        return {
            "chunk_size": 500,
            "chunk_overlap": 50,
        }

    @abstractmethod
    def chunk(self, data_model: CleanedDocumentT) -> list[ChunkT]:
        pass #not defining here for future doc specific chunking


class TranscriptChunkingHandler(ChunkingDataHandler):
    @property
    def metadata(self) -> dict:
        return {
            "chunk_size": 250,
            "chunk_overlap": 25,
        }

    def chunk(self, data_model: CleanedTranscriptDocument) -> list[TranscriptChunk]:
        data_models_list = []

        cleaned_content = data_model.content
        chunks = chunk_text(
            cleaned_content, chunk_size=self.metadata["chunk_size"], chunk_overlap=self.metadata["chunk_overlap"]
        )

        for idx, chunk_content in enumerate(chunks):
            chunk_hash = hashlib.md5(chunk_content.encode('utf-8')).hexdigest()
            model = TranscriptChunk(
                chunk_id=chunk_hash,
                content=chunk_content,
                chunk_index=idx,
                dataset_id=data_model.dataset_id,
                platform=data_model.platform,
                document_id=data_model.id,
                link=data_model.link,
                author_id=data_model.author_id,
                author_full_name=data_model.author_full_name,
                metadata=self.metadata,
            )
            data_models_list.append(model)

        return data_models_list


class ArticleChunkingHandler(ChunkingDataHandler):
    @property
    def metadata(self) -> dict:
        return {
            "min_length": 1000,
            "max_length": 2000,
        }

    def chunk(self, data_model: CleanedArticleDocument) -> list[ArticleChunk]:
        data_models_list = []

        cleaned_content = data_model.content
        chunks = chunk_article(
            cleaned_content, min_length=self.metadata["min_length"], max_length=self.metadata["max_length"]
        )

        for idx, chunk_content in enumerate(chunks):
            chunk_hash = hashlib.md5(chunk_content.encode('utf-8')).hexdigest()
            model = ArticleChunk(
                chunk_id=chunk_hash,
                chunk_index=idx,
                content=chunk_content,
                dataset_id=data_model.dataset_id,
                platform=data_model.platform,
                link=data_model.link,
                document_id=data_model.id,
                author_id=data_model.author_id,
                author_full_name=data_model.author_full_name,
                metadata=self.metadata,
            )
            data_models_list.append(model)

        return data_models_list
