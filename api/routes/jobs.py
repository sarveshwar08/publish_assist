from fastapi import APIRouter, HTTPException

from ..schema.job import JobDoc
from ..services.job_service import JobService
from ..services.integration_service import IntegrationService
from ..services.dataset_service import DatasetService
from ..services.generate_service import GenerateService

from ..types import JobType

from api.db import mongo_db

router = APIRouter(prefix="/v1", tags=["jobs"])

@router.get("/jobs/{job_id}")
def get_job(job_id: str):

    jobs_col = mongo_db["jobs"]
    datasets_col = mongo_db["datasets"]

    job_service = JobService(jobs_col)
    dataset_service = DatasetService(datasets_col)
    zenml_service = IntegrationService()

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
                if job.type == JobType.INGEST:
                    stage = (job.progress.stage or "").lower()
                    step_runs = job.zenml.step_run_ids or {}

                    if stage != "feature_engineering" and "feature_engineering" not in step_runs:
                        ingestion_run_id = job.zenml.run_id
                        try:
                            fe_ref = zenml_service.start_feature_engineering_pipeline(dataset_id=job.dataset_id)
                            job_service.transition_to_feature_engineering(
                                job_id=job_id,
                                ingestion_run_id=ingestion_run_id,
                                feature_run_id=fe_ref["run_id"],
                                feature_run_url=fe_ref.get("run_url"),
                            )
                        except Exception as e:
                            job_service.mark_failed(
                                job_id=job_id,
                                code="FEATURE_ENGINEERING_START_FAILED",
                                message=str(e),
                            )
                    else:
                        dataset_service.mark_ready(job.dataset_id)
                        job_service.mark_completed(job_id=job_id, message="Feature engineering completed")
                elif job.type == JobType.GENERATE:
                    gen_service = GenerateService()
                    output = gen_service.load_generated_output(job.zenml.run_id)
                    job_service.set_result(job_id=job_id, result={"output": output})
                    job_service.mark_completed(job_id=job_id, message="Generation completed")
                else:
                    job_service.mark_completed(job_id=job_id, message="Job completed")

            elif normalized == "FAILED":
                job_service.mark_failed(job_id=job_id, code="ZENML_RUN_FAILED", message="ZenML pipeline failed")
        except Exception:
            pass

    updated = job_service.get_job(job_id)
    return JobDoc.from_mongo(updated).model_dump()
