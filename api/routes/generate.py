from fastapi import APIRouter, HTTPException
from ..schema.request import GenerateRequest, GenerateResponse
from api.services.generate_service import GenerateService
from api.services.job_service import JobService
from api.services.dataset_service import DatasetService
from api.db import mongo_db
from api.types import JobType

router = APIRouter(prefix="/v1", tags=["generation"])

@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    jobs_col = mongo_db["jobs"]
    datasets_col = mongo_db["datasets"]

    job_service = JobService(jobs_col)
    dataset_service = DatasetService(datasets_col)
    gen_service = GenerateService()

    dataset = dataset_service.get_by_id(req.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.ready:
        raise HTTPException(status_code=400, detail="Dataset is not ready yet")

    job_doc = job_service.create_job(
        job_type=JobType.GENERATE,
        user_id=dataset.user_id,
        dataset_id=req.dataset_id,
        source_config=dataset.source_config,
        pipeline_name="inference_pipeline",
    )

    try:
        run_ref = gen_service.start_generation_pipeline(
            dataset_id=req.dataset_id,
            topic=req.topic,
            platform=str(req.platform),
            tone=str(req.tone),
            use_web=req.use_web,
        )
        job_service.attach_zenml_run(
            job_id=job_doc.id,
            run_id=run_ref["run_id"],
            run_url=run_ref.get("run_url"),
        )
    except Exception as e:
        job_service.mark_failed(job_id=job_doc.id, code="ZENML_START_FAILED", message=str(e))
        raise HTTPException(status_code=500, detail="Failed to start generation pipeline")

    return GenerateResponse(
        output="",
        sources=[],
        debug={
            "job_id": job_doc.id,
            "run_id": run_ref["run_id"],
            "run_url": run_ref.get("run_url"),
        },
    )
