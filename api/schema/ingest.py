from pydantic import BaseModel
from typing import Optional

class IngestRequest(BaseModel):
    substack_username: Optional[str] = None
    medium_username: Optional[str] = None
    youtube_handle: Optional[str] = None