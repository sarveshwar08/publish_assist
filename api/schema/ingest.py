from pydantic import BaseModel
from typing import Optional

class IngestRequest(BaseModel):
    user_full_name: str
    substack_username: Optional[str] = None
    youtube_handle: Optional[str] = None