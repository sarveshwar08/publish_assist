from pymongo.collection import Collection
from ..schema.dataset import DatasetDoc

from ..helper import make_id

class DatasetService:
    def __init__(self, datasets_col: Collection):
        self.datasets = datasets_col

    def create(self, *, user_id: str, source_config: dict) -> DatasetDoc:
        dataset = DatasetDoc(id=make_id("ds"), user_id=user_id, source_config=source_config)
        self.datasets.insert_one(dataset.to_mongo())
        return dataset.id

    def mark_ready(self, dataset_id: str, stats_delta: dict | None = None):
        update = {"$set": {"ready": True}}
        if stats_delta:
            update["$inc"] = {f"stats.{k}": v for k, v in stats_delta.items()}
        self.datasets.update_one({"_id": dataset_id}, update)
        
    def set_links_found(self, dataset_id: str, links_found: int):
        self.datasets.update_one(
            {"_id": dataset_id},
            {"$set": {"stats.links_found": int(links_found)}}
        )

    def get_by_user(self, user_id: str):
        cursor = self.datasets.find({"user_id": user_id}).sort("created_at", -1)
        return [DatasetDoc.from_mongo(doc) for doc in cursor]

    def get_by_id(self, dataset_id: str) -> DatasetDoc | None:
        doc = self.datasets.find_one({"_id": dataset_id})
        if not doc:
            return None
        return DatasetDoc.from_mongo(doc)
