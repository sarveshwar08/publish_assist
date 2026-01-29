from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class DatasetDoc(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    
    id: str = Field(validation_alias="_id")

    user_id: str
    source_config: Dict[str, Any]

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ready: bool = False

    stats: Dict[str, int] = Field(default_factory=dict)

    def to_mongo(self) -> dict:
        doc = self.model_dump()
        doc["_id"] = doc.pop("id")
        return doc

    @classmethod
    def from_mongo(cls, doc: dict) -> "DatasetDoc":
        return cls.model_validate(doc)
