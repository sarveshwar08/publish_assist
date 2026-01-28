from fastapi import APIRouter, HTTPException
from publish_assist.domain.eval import EvalRun

router = APIRouter(prefix="/debug/eval", tags=["Debug Evaluation"])

@router.get("/latest")
def get_latest_eval_run(dataset_id: str):

    runs = EvalRun.bulk_find(dataset_id=dataset_id)
    
    if not runs:
         raise HTTPException(status_code=404, detail="No eval runs found for dataset")
         
    runs.sort(key=lambda x: x.created_at, reverse=True)
    
    return runs[0].model_dump()

@router.get("/{eval_run_id}")
def get_eval_run(eval_run_id: str):
    # We query by _id because NoSQLBaseDocument stores id as _id in Mongo
    run = EvalRun.find(_id=eval_run_id)
    
    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found")
    
    return run.model_dump()
