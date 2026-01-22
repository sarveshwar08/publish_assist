from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone

from ..types import JobStatus, JobType

class JobError(BaseModel):
    at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class JobProgress(BaseModel):
    stage: str = "queued"
    message: Optional[str] = "Waiting to start"

class JobStats(BaseModel):
    docs_found: int = 0
    docs_inserted: int = 0
    chunks_created: int = 0
    vectors_upserted: int = 0

class PipelineRef(BaseModel):
    pipeline_name: Optional[str] = None
    run_id: Optional[str] = None
    run_url: Optional[str] = None
    step_run_ids: Dict[str, str] = Field(default_factory=dict)

class JobTiming(BaseModel):
    created_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
class JobPolling(BaseModel):
    last_polled_at: Optional[datetime] = None
    poll_count: int = 0

class JobDoc(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    
    id: str = Field(alias="_id")

    type: JobType
    status: JobStatus = JobStatus.QUEUED

    user_id: str
    dataset_id: str

    source_config: Dict[str, Any] = Field(default_factory=dict)

    zenml: PipelineRef = Field(default_factory=PipelineRef)
    progress: JobProgress = Field(default_factory=JobProgress)
    stats: JobStats = Field(default_factory=JobStats)
    errors: List[JobError] = Field(default_factory=list)
    timing: JobTiming = Field(default_factory=JobTiming)
    polling: JobPolling = Field(default_factory=JobPolling)
    
    @classmethod
    def from_mongo(cls, doc) -> "JobDoc":
        return cls.model_validate(doc)
    
    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True)
