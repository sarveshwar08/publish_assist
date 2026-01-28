from abc import ABC
from typing import Optional
from datetime import datetime, timezone

from pydantic import UUID4, Field

from publish_assist.domain.base import VectorBaseDocument
from publish_assist.domain.types import DataCategory


class Chunk(VectorBaseDocument, ABC):
    content: str
    dataset_id: str
    chunk_id: str
    chunk_index: int
    platform: str
    document_id: UUID4
    author_id: UUID4
    author_full_name: str
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)

class ArticleChunk(Chunk):
    link: str

    class Config:
        category = DataCategory.ARTICLES
        
        
class TranscriptChunk(Chunk):
    link: str

    class Config:
        category = DataCategory.TRANSCRIPTS
