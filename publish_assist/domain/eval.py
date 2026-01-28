from datetime import datetime
from typing import List, Dict, Any

from pydantic import UUID4, Field, BaseModel

from publish_assist.domain.base.nosql import NoSQLBaseDocument
from publish_assist.domain.types import DataCategory

class EvalQuery(NoSQLBaseDocument):
    dataset_id: str
    query: str
    relevant_chunk_ids: List[str]
    document_id: UUID4

    class Settings:
        name = DataCategory.EVAL_QUERIES

class PerQueryMetric(BaseModel):
    query: str
    recall_at_k: float = Field(alias=f"recall@k") # We might need dynamic aliases or just keys in dict
    precision_at_k: float = Field(alias=f"precision@k")
    retrieved_chunk_ids: List[str]
    relevant_chunk_ids: List[str]

    # To handle dynamic @k in field names, we might just store as dict in the parent, 
    # but the prompt specifies schema. 
    # "recall@10": 1.0
    # Let's use a dict for simplicity in the parent list, or a flexible model.
    # The prompt example:
    # {
    #   "query": "...",
    #   "recall@10": 1.0,
    #   "precision@10": 0.3,
    #   "retrieved_chunk_ids": [...],
    #   "relevant_chunk_ids": [...]
    # }
    
class EvalRun(NoSQLBaseDocument):
    dataset_id: str
    top_k: int
    metrics: Dict[str, float]
    per_query: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = DataCategory.EVAL_RUNS
