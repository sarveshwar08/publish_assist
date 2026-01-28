from zenml import step
import json
from pathlib import Path
from loguru import logger
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny

from publish_assist.infra.db.qdrant import get_qdrant_client
from publish_assist.application.networks.embeddings import EmbeddingModelSingleton
from publish_assist.domain.types import STYLE_PLATFORM_MAP, RetrievalType

@step
def retrieve_chunks(
    dataset_id: str,
    queries: list[str],
    platform: str,
    kind: str,
    top_k: int = 10,
) -> dict:
    client = get_qdrant_client()
    embedder = EmbeddingModelSingleton()

    must = [FieldCondition(key="dataset_id", match=MatchValue(value=dataset_id))]

    if kind == RetrievalType.STYLE:
        must.append(
            FieldCondition(
                key="platform",
                match=MatchAny(any=STYLE_PLATFORM_MAP[platform]),
            )
        )

    qfilter = Filter(must=must)

    collection_names = ["embedded_articles", "embedded_transcripts"]

    all_hits = []

    logger.info('start matching points')
    for q in queries:
        qvec = embedder.embed(q)
        for collection_name in collection_names:
            response = client.query_points(
                collection_name=collection_name,
                query=qvec,
                query_filter=qfilter,
                limit=top_k,
                with_payload=True,
            )
            for hit in response.points:
                all_hits.append((collection_name, hit))

    best_by_chunk_id: dict[str, dict] = {}
    for collection_name, h in all_hits:
        payload = h.payload or {}
        chunk_id = str(h.id) #since we set the id as the chunk_id itself

        result = {
            "chunk_id": chunk_id,
            "doc_id": payload.get("document_id"),
            "text": payload.get("content"),
            "score": float(h.score),
            "collection": collection_name,
        }

        existing = best_by_chunk_id.get(chunk_id)
        if existing is None or result["score"] > existing["score"]:
            best_by_chunk_id[chunk_id] = result

    logger.info(f"Dedup stats: best chunks number {len(best_by_chunk_id.keys())},  hits number {len(all_hits)}")

    results = list(best_by_chunk_id.values())

    results.sort(key=lambda x: x["score"], reverse=True)

    return {"kind": kind, "chunks": results[:top_k]}
