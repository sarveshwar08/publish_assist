from loguru import logger
from typing_extensions import Annotated
from zenml import step

from publish_assist.utils.general import batch
from publish_assist.domain.base import VectorBaseDocument


@step(enable_cache=False)
def load_to_vector_db(
    documents: Annotated[list, "documents"],
    dataset_id
) -> Annotated[bool, "successful"]:
    logger.info(f"Loading {len(documents)} documents into the vector database.")

    grouped_documents = VectorBaseDocument.group_by_class(documents)
    for document_class, documents in grouped_documents.items():
        logger.info(f"Loading documents into {document_class.get_collection_name()}")
        for documents_batch in batch(documents, size=4):
            try:
                document_class.bulk_insert(documents_batch)
            except Exception:
                logger.error(f"Failed to insert documents into {document_class.get_collection_name()}")

                return False

    return True
