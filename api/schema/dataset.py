from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DatasetDoc(BaseModel):
    id: str = Field(alias="_id")

    user_id: str
    source_config: Dict[str, Any]

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ready: bool = False

    stats: Dict[str, int] = Field(default_factory=dict)

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True)

    @classmethod
    def from_mongo(cls, doc: dict) -> "DatasetDoc":
        return cls.model_validate(doc)
