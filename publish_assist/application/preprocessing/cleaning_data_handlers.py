from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from publish_assist.domain.cleaned_documents import (
    CleanedDocument,
    CleanedArticleDocument,
    CleanedTranscriptDocument,
)
from publish_assist.domain.documents import (
    Document,
    TranscriptDocument,
    ArticleDocument
)

from .operations import clean_text

DocumentT = TypeVar("DocumentT", bound=Document)
CleanedDocumentT = TypeVar("CleanedDocumentT", bound=CleanedDocument)


class CleaningDataHandler(ABC, Generic[DocumentT, CleanedDocumentT]):
    @abstractmethod
    def clean(self, data_model: DocumentT) -> CleanedDocumentT:
        pass

#TODO: P2 add document specific functions during more elaborate feature eng
class TranscriptCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: TranscriptDocument) -> CleanedTranscriptDocument:
        valid_content = [content for content in data_model.content.values() if content]
        
        return CleanedTranscriptDocument(
            id=data_model.id,
            dataset_id=data_model.dataset_id,
            content=clean_text(" #### ".join(valid_content)),
            platform=data_model.platform,
            link=data_model.link,
            author_id=data_model.author_id,
            author_full_name=data_model.author_full_name,
        )


class ArticleCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: ArticleDocument) -> CleanedArticleDocument:
        valid_content = [content for content in data_model.content.values() if content]

        return CleanedArticleDocument(
            id=data_model.id,
            dataset_id=data_model.dataset_id,
            content=clean_text(" #### ".join(valid_content)),
            platform=data_model.platform,
            link=data_model.link,
            author_id=data_model.author_id,
            author_full_name=data_model.author_full_name,
        )