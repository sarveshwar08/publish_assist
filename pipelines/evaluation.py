from zenml import pipeline
from steps.evaluation.generate_dataset import generate_eval_dataset
from steps.evaluation.evaluate_retrieval import retrieval_evaluation

@pipeline
def rag_retrieval_evaluation_pipeline(
    dataset_id: str,
    top_k: int = 10,
    n_documents: int = 5,
    chunks_per_doc: int = 2,
    queries_per_chunk: int = 2
):
    dataset_id_out = generate_eval_dataset(
        dataset_id=dataset_id,
        n_documents=n_documents,
        chunks_per_doc=chunks_per_doc,
        queries_per_chunk=queries_per_chunk
    )
    
    retrieval_evaluation(
        dataset_id=dataset_id_out,
        top_k=top_k,
    )
