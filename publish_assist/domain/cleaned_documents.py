from abc import ABC
from typing import Optional

from pydantic import UUID4

from .base import VectorBaseDocument
from .types import DataCategory


class CleanedDocument(VectorBaseDocument, ABC):
    content: str
    dataset_id: str
    platform: str
    author_id: UUID4
    author_full_name: str


class CleanedTranscriptDocument(CleanedDocument):
    link: str

    class Config:
        name = "cleaned_transcripts"
        category = DataCategory.TRANSCRIPTS
        use_vector_index = False


class CleanedArticleDocument(CleanedDocument):
    link: str

    class Config:
        name = "cleaned_articles"
        category = DataCategory.ARTICLES
        use_vector_index = False
