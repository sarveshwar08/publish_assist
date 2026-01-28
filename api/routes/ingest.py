from fastapi import APIRouter, Depends, HTTPException
import hashlib

from api.services.job_service import JobService
from api.services.dataset_service import DatasetService
from api.services.integration_service import IntegrationService
from api.schema.ingest import IngestRequest

from api.db import mongo_db
from ..types import JobType

router = APIRouter(prefix="/v1", tags=["ingest"])

@router.post("/ingest")
def ingest(req: IngestRequest):
    # TODO: P2 -  replace user_id with auth extracted user
    user_id = hashlib.md5((req.user_full_name).encode('utf-8')).hexdigest()

    if not (req.substack_username or req.medium_username or req.youtube_handle):
        raise HTTPException(status_code=400, detail="Provide at least one source username/handle")

    source_config = {
        "substack": {"username": req.substack_username, "enabled": bool(req.substack_username)},
        "medium": {"username": req.medium_username, "enabled": bool(req.medium_username)},
        "youtube": {"handle": req.youtube_handle, "enabled": bool(req.youtube_handle)},
    }

    jobs_col = mongo_db["jobs"]
    datasets_col = mongo_db["datasets"]

    job_service = JobService(jobs_col)
    dataset_service = DatasetService(datasets_col)
    zenml_service = IntegrationService()

    ds_id = dataset_service.create(
        user_id=user_id,
        source_config=source_config,
    )

    job_doc = job_service.create_job(
        job_type=JobType.INGEST,
        user_id=user_id,
        dataset_id=ds_id,
        source_config=source_config,
        pipeline_name="etl_pipeline",
    )
    job_id = job_doc.id

    # start pipeline
    try:
        run_ref = zenml_service.start_ingestion_pipeline(source_config=source_config, dataset_id=ds_id, user_full_name=req.user_full_name)
        job_service.attach_zenml_run(job_id=job_id, run_id=run_ref["run_id"], run_url=run_ref.get("run_url"))
        dataset_service.set_links_found(ds_id, run_ref.get("links_found", 0))
    except Exception as e:
        job_service.mark_failed(job_id=job_id, code="ZENML_START_FAILED", message=str(e))
        raise HTTPException(status_code=500, detail="Failed to start ingestion pipeline")

    return {"job_id": job_id, "dataset_id": ds_id}
