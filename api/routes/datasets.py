from typing import List
from fastapi import APIRouter, HTTPException

from api.schema.dataset import DatasetDoc
from api.services.dataset_service import DatasetService
from api.db import mongo_db

router = APIRouter(prefix="/v1", tags=["datasets"])

@router.get("/datasets", response_model=List[DatasetDoc])
def get_datasets(user_id: str):
    datasets_col = mongo_db["datasets"]
    dataset_service = DatasetService(datasets_col)
    
    return dataset_service.get_by_user(user_id)
