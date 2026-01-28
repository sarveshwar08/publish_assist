from fastapi import FastAPI

from api.routes.ingest import router as ingest_router
from api.routes.jobs import router as jobs_router
from api.routes.generate import router as generate_router
from api.routes.health import router as health_router
from api.routes.datasets import router as datasets_router
from api.routes.debug_eval import router as debug_eval_router

app = FastAPI(title="Publish Assist API")

app.include_router(ingest_router)
app.include_router(jobs_router)
app.include_router(generate_router)
app.include_router(health_router)
app.include_router(datasets_router)
app.include_router(debug_eval_router)
