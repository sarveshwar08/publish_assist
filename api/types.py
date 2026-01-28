from enum import StrEnum

class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    
class JobType(StrEnum):
    INGEST = "INGEST"
    GENERATE = "GENERATE"
    EVAL = "EVAL"
    REINDEX = "REINDEX"
