from fastapi import FastAPI
# import settings here
from db.mongo import get_mongo

from api.routes.ingest import router as ingest_router
from api.routes.jobs import router as jobs_router

app = FastAPI(title="LLM Pipeline API")

mongo_db = get_mongo(settings.MONGO_URL, settings.MONGO_DB)

app.include_router(ingest_router)
app.include_router(jobs_router)

@app.get("/health")
def health():
    return {"status": "ok"}
