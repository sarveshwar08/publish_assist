import random
from zenml import step
from loguru import logger
from publish_assist.domain.documents import ArticleDocument, TranscriptDocument
from publish_assist.domain.chunks import ArticleChunk, TranscriptChunk
from publish_assist.domain.eval import EvalQuery
from publish_assist.infra.llm import LlamaClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

@step
def generate_eval_dataset(
    dataset_id: str,
    n_documents: int = 5,
    chunks_per_doc: int = 2,
    queries_per_chunk: int = 2
) -> str:
    docs = []
    
    articles = ArticleDocument.bulk_find(dataset_id=dataset_id)
    transcripts = TranscriptDocument.bulk_find(dataset_id=dataset_id)
    
    all_docs = articles + transcripts
    
    if not all_docs:
        logger.warning(f"No documents found for dataset_id: {dataset_id}")
        return dataset_id

    if len(all_docs) > n_documents:
        sampled_docs = random.sample(all_docs, n_documents)
    else:
        sampled_docs = all_docs
        
    logger.info(f"Sampled {len(sampled_docs)} documents for evaluation.")

    llm = LlamaClient()
    
    for doc in sampled_docs:
        chunk_cls = None
        if isinstance(doc, ArticleDocument):
            chunk_cls = ArticleChunk
        elif isinstance(doc, TranscriptDocument):
            chunk_cls = TranscriptChunk
        else:
            continue
            
        # 2. Get chunks for document
        qfilter = Filter(
            must=[
                FieldCondition(key="dataset_id", match=MatchValue(value=dataset_id)),
                FieldCondition(key="document_id", match=MatchValue(value=str(doc.id)))
            ]
        )
        
        # limit 100 per doc for sampling
        chunks, _ = chunk_cls.bulk_find(limit=100, query_filter=qfilter)
        
        if not chunks:
            logger.warning(f"No chunks found for document {doc.id}")
            continue
            
        if len(chunks) > chunks_per_doc:
            selected_chunks = random.sample(chunks, chunks_per_doc)
        else:
            selected_chunks = chunks
            
        for chunk in selected_chunks:
            prompt = f"""
            You are an expert at creating evaluation queries for retrieval systems.
            Given the following text chunk, generate {queries_per_chunk} distinct search queries that a user might ask, for which this chunk would be the perfect answer.
            The queries should be specific enough to retrieve this content but natural.
            Output ONLY the queries, one per line. Do not number them.
            
            Text Chunk:
            {chunk.content[:2000]}
            """
            
            try:
                response = llm.generate(prompt)
                queries = [q.strip() for q in response.split('\n') if q.strip()]
                
                # Take only requested amount
                queries = queries[:queries_per_chunk]
                
                for q in queries:
                    # 4. Save EvalQuery
                    eval_query = EvalQuery(
                        dataset_id=dataset_id,
                        query=q,
                        relevant_chunk_ids=[chunk.chunk_id],
                        document_id=doc.id
                    )
                    eval_query.save()
                    logger.debug(f"Saved eval query: {q}")
                    
            except Exception as e:
                logger.error(f"Failed to generate queries for chunk {chunk.chunk_id}: {e}")

    logger.info(f"Evaluation dataset generation complete for {dataset_id}")
    return dataset_id
