from abc import ABC

from pydantic import UUID4, Field

from publish_assist.domain.types import DataCategory

from .base import VectorBaseDocument


class EmbeddedChunk(VectorBaseDocument, ABC):
    content: str
    chunk_id: str
    chunk_index: int
    dataset_id: str
    embedding: list[float] | None
    platform: str
    document_id: UUID4
    author_id: UUID4
    author_full_name: str
    metadata: dict = Field(default_factory=dict)

class EmbeddedTranscriptChunk(EmbeddedChunk):
    link: str

    class Config:
        name = "embedded_transcripts"
        category = DataCategory.TRANSCRIPTS
        use_vector_index = True


class EmbeddedArticleChunk(EmbeddedChunk):
    link: str

    class Config:
        name = "embedded_articles"
        category = DataCategory.ARTICLES
        use_vector_index = True
