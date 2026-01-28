from zenml import step
from loguru import logger
from publish_assist.domain.eval import EvalQuery, EvalRun
from publish_assist.infra.db.qdrant import get_qdrant_client
from publish_assist.application.networks.embeddings import EmbeddingModelSingleton
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

def compute_metrics(relevant: list[str], retrieved: list[str], k: int) -> tuple[float, float]:
    retrieved_k = retrieved[:k]
    relevant_set = set(relevant)
    retrieved_set = set(retrieved_k)
    
    hits = relevant_set.intersection(retrieved_set)
    
    recall = len(hits) / len(relevant_set) if relevant_set else 0.0
    precision = len(hits) / k if k > 0 else 0.0
    
    return recall, precision

@step
def retrieval_evaluation(
    dataset_id: str,
    top_k: int = 10
) -> None:
    queries = EvalQuery.bulk_find(dataset_id=dataset_id)
    if not queries:
        logger.warning(f"No evaluation queries found for dataset_id: {dataset_id}")
        return

    client = get_qdrant_client()
    embedder = EmbeddingModelSingleton()
    
    per_query_results = []
    total_recall = 0.0
    total_precision = 0.0
    
    for eq in queries:
        qvec = embedder.embed(eq.query)
        
        must = [FieldCondition(key="dataset_id", match=MatchValue(value=dataset_id))]
        
        qfilter = Filter(must=must)
        
        collection_names = ["embedded_articles", "embedded_transcripts"]

        all_points = []
        for collection_name in collection_names:
            response = client.query_points(
                collection_name=collection_name,
                query=qvec,
                query_filter=qfilter,
                limit=top_k,
                with_payload=True,
            )
            all_points.extend(response.points)
        
        retrieved_chunk_ids = []
        for h in all_points:
            c_id = h.payload.get("chunk_id") if h.payload else None
            if not c_id:
                c_id = str(h.id)
            retrieved_chunk_ids.append(c_id)
        
        recall, precision = compute_metrics(eq.relevant_chunk_ids, retrieved_chunk_ids, top_k)
        
        total_recall += recall
        total_precision += precision
        
        per_query_results.append({
            "query": eq.query,
            f"recall@{top_k}": recall,
            f"precision@{top_k}": precision,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "relevant_chunk_ids": eq.relevant_chunk_ids
        })

    n = len(queries)
    mean_recall = total_recall / n if n > 0 else 0.0
    mean_precision = total_precision / n if n > 0 else 0.0
    
    metrics = {
        f"mean_recall@{top_k}": mean_recall,
        f"mean_precision@{top_k}": mean_precision
    }
    
    eval_run = EvalRun(
        dataset_id=dataset_id,
        top_k=top_k,
        metrics=metrics,
        per_query=per_query_results
    )
    eval_run.save()
    
    logger.info(f"Evaluation complete. Mean Recall@{top_k}: {mean_recall:.4f}, Mean Precision@{top_k}: {mean_precision:.4f}")
