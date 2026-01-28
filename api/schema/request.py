from pydantic import BaseModel, Field
from typing import Literal, Optional, Any, Dict, List
from publish_assist.domain.types import Platform, Tone 

class GenerateRequest(BaseModel):
    dataset_id: str
    topic: str
    platform: Platform
    tone: Tone = Tone.INFORMATIVE
    use_web: bool = False

class SourceItem(BaseModel):
    doc_id: str
    chunk_id: str
    score: float

class GenerateResponse(BaseModel):
    output: str
    sources: List[SourceItem] = Field(default_factory=list)
    debug: Dict[str, Any] = Field(default_factory=dict)