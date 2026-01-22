from fastapi import APIRouter, HTTPException
from schema.job import JobDoc
from services.job_service import JobService
from services.integration_service import IntegrationService
from services.dataset_service import DatasetService

from api.main import mongo_db

router = APIRouter(prefix="/v1", tags=["jobs"])

@router.get("/jobs/{job_id}")
def get_job(job_id: str):

    jobs_col = mongo_db["jobs"]
    datasets_col = mongo_db["datasets"]

    job_service = JobService(jobs_col)
    dataset_service = DatasetService(datasets_col)
    zenml_service = ZenMLService()

    job_service.touch_polling(job_id)

    job_doc = job_service.get_job(job_id)
    if not job_doc:
        raise HTTPException(status_code=404, detail="Job not found")

    job = JobDoc.from_mongo(job_doc)

    if job.zenml.run_id and job.status in ("QUEUED", "RUNNING"):
        try:
            zenml_data = zenml_service.get_run_status(job.zenml.run_id)
            normalized = zenml_service.normalize_status(zenml_data["status"])

            if normalized == "COMPLETED":
                # mark dataset ready
                dataset_service.mark_ready(job.dataset_id)
                job_service.mark_completed(job_id, message="Ingestion completed")

            elif normalized == "FAILED":
                job_service.mark_failed(job_id, code="ZENML_RUN_FAILED", message="ZenML pipeline failed")
        except Exception:
            pass

    updated = job_service.get_job(job_id)
    return JobDoc.from_mongo(updated).model_dump()
