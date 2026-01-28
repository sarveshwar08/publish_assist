from loguru import logger
from typing_extensions import Annotated
from zenml import get_step_context, step
from concurrent.futures import ThreadPoolExecutor, as_completed

from publish_assist.domain.documents import Document, TranscriptDocument, ArticleDocument, NoSQLBaseDocument, UserDocument

@step
def query_data_warehouse(
    dataset_id: str,
) -> Annotated[list, "raw_documents"]:
    logger.info(f"Querying data warehouse for dataset_id={dataset_id}")
    
    results = fetch_all_data(dataset_id)
    user_documents = [doc for query_result in results.values() for doc in query_result]

    user_full_name = "Unknown"
    if user_documents:
        # Assuming all documents in the dataset belong to the same user
        user_full_name = getattr(user_documents[0], "author_full_name", "Unknown")

    for d in user_documents:
        if getattr(d, "dataset_id", None) != dataset_id:
            logger.warning(f"Found document with mismatched dataset_id: {d.id}")

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="raw_documents",
        metadata={
            "user_full_name": user_full_name,
            "dataset_id": dataset_id,
            **_get_metadata(user_documents)
        },
    )

    return user_documents   


def fetch_all_data(dataset_id: str) -> dict[str, list[NoSQLBaseDocument]]:
    with ThreadPoolExecutor() as executor:
        future_to_query = {
            executor.submit(__fetch_articles, dataset_id): "articles",
            executor.submit(_fetch_transcripts, dataset_id): "transcripts",
        }

        results = {}
        for future in as_completed(future_to_query):
            query_name = future_to_query[future]
            try:
                results[query_name] = future.result()
            except Exception:
                logger.exception(f"'{query_name}' request failed.")

                results[query_name] = []

    return results


def __fetch_articles(dataset_id) -> list[NoSQLBaseDocument]:
    return ArticleDocument.bulk_find(dataset_id=dataset_id)


def _fetch_transcripts(dataset_id) -> list[NoSQLBaseDocument]:
    return TranscriptDocument.bulk_find(dataset_id=dataset_id)


def _get_metadata(documents: list[Document]) -> dict:
    metadata = {
        "num_documents": len(documents),
    }
    for document in documents:
        collection = document.get_collection_name()
        if collection not in metadata:
            metadata[collection] = {}

        metadata[collection]["num_documents"] = metadata[collection].get("num_documents", 0) + 1

    return metadata
