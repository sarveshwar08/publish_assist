from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pymongo.collection import Collection
import uuid

from ..schema.job import JobDoc, PipelineRef
from ..types import JobStatus, JobType
from ..helper import make_id

class JobService:
    def __init__(self, jobs_col: Collection):
        self.jobs = jobs_col

    def create_job(self, *, job_type: str, user_id: str, dataset_id: str, source_config: dict, pipeline_name: str) -> JobDoc:
        job = JobDoc(
            id=make_id(f"job_{job_type}"),
            type=job_type,
            user_id=user_id,
            dataset_id=dataset_id,
            source_config=source_config,
            zenml=PipelineRef(pipeline_name=pipeline_name)
        )
        self.jobs.insert_one(job.to_mongo())
        return job

    def attach_zenml_run(self, *, job_id: str, run_id: str, run_url: Optional[str] = None):
        update = {
            "$set": {
                "zenml.run_id": run_id,
                "zenml.run_url": run_url,
                "status": JobStatus.RUNNING,
                "progress.stage": "running",
                "timing.started_at": datetime.now(timezone.utc),
            }
        }
        self.jobs.update_one({"_id": job_id}, update)

    def mark_progress(
        self,
        *,
        job_id: str,
        stage: str,
        message: Optional[str] = None,
        stats_delta: Optional[Dict[str, int]] = None
    ):
        update = {
            "$set": {
                "progress.stage": stage,
                **({"progress.message": message} if message else {})
            }
        }
        if stats_delta:
            update["$inc"] = {f"stats.{k}": v for k, v in stats_delta.items()}

        self.jobs.update_one({"_id": job_id}, update)

    def mark_failed(self, *, job_id: str, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        now = datetime.now(timezone.utc)
        update = {
            "$set": {
                "status": JobStatus.FAILED,
                "progress.stage": "failed",
                "progress.message": message,
                "timing.finished_at": now,
            },
            "$push": {
                "errors": {
                    "at": now,
                    "code": code,
                    "message": message,
                    "details": details or {}
                }
            }
        }
        self.jobs.update_one({"_id": job_id}, update)

    def mark_completed(self, *, job_id: str, message: str = "Completed"):
        now = datetime.now(timezone.utc)

        job = self.jobs.find_one({"_id": job_id}, {"timing.started_at": 1})
        started_at = (job or {}).get("timing", {}).get("started_at")
        duration_ms = None
        if started_at:
            duration_ms = int((now - started_at).total_seconds() * 1000)

        update = {
            "$set": {
                "status": JobStatus.COMPLETED,
                "progress.stage": "completed",
                "progress.message": message,
                "timing.finished_at": now,
                "timing.duration_ms": duration_ms,
            }
        }
        self.jobs.update_one({"_id": job_id}, update)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.find_one({"_id": job_id})

    def touch_polling(self, job_id: str):
        now = datetime.now(timezone.utc)
        self.jobs.update_one(
            {"_id": job_id},
            {"$set": {"polling.last_polled_at": now}, "$inc": {"polling.poll_count": 1}}
        )
