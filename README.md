  # Publish Assist

  **Publish Assist** is a RAG-powered content assistant that helps creators generate *original* posts in their own style by:
  1) ingesting source material (Substack + YouTube),
  2) extracting/embedding knowledge into a vector store,
  3) retrieving + reranking relevant chunks at generation time, and
  4) producing platform-specific drafts via an LLM—while explicitly avoiding copying.

  Used:
  - a **FastAPI** backend ([api/main.py](api/main.py)) that orchestrates jobs and pipelines,
  - a **Streamlit** demo UI ([ui/app.py](ui/app.py)),
  - **ZenML** pipelines for ingestion, feature engineering, inference, and retrieval evaluation ([pipelines/](pipelines/)).

  ---

  ## High-level architecture

  ```mermaid
  flowchart LR
    UI[Streamlit UI<br/>ui/] --> API[FastAPI<br/>api/]
    API --> JOBS[(MongoDB<br/>jobs/datasets)]
    API --> ZEN[ZenML Pipelines<br/>pipelines/]
    ZEN --> MONGO[(MongoDB<br/>raw docs + eval runs)]
    ZEN --> QDR[(Qdrant<br/>embeddings)]
    ZEN --> LLM[Groq LLM<br/>publish_assist/infra/llm.py]
    QDR --> ZEN
  ```

  ### Key modules
  - **API**
    - App entrypoint: [`api.main.app`](api/main.py)
    - Ingestion endpoint: [api/routes/ingest.py](api/routes/ingest.py)
    - Generation endpoint: [api/routes/generate.py](api/routes/generate.py)
    - Job tracking/polling: [api/routes/jobs.py](api/routes/jobs.py), [`api.services.job_service.JobService`](api/services/job_service.py)
    - Dataset state: [`api.services.dataset_service.DatasetService`](api/services/dataset_service.py)
    - ZenML bridge: [`api.services.integration_service.IntegrationService`](api/services/integration_service.py)

  - **Pipelines (ZenML)**
    - Ingest links + persist docs: [`pipelines.digital_data_etl.digital_data_etl`](pipelines/digital_data_etl.py)
    - Feature engineering (clean → chunk → embed → load): [`pipelines.feature_engineering.feature_engineering`](pipelines/feature_engineering.py)
    - RAG inference: [`pipelines.inference.generate_content_pipeline`](pipelines/inference.py)
    - Retrieval evaluation: [`pipelines.evaluation.rag_retrieval_evaluation_pipeline`](pipelines/evaluation.py)

  - **Storage**
    - Mongo-backed documents via [`publish_assist.domain.base.nosql.NoSQLBaseDocument`](publish_assist/domain/base/nosql.py)
    - Qdrant-backed vectors via [`publish_assist.domain.base.vector.VectorBaseDocument`](publish_assist/domain/base/vector.py)

  ---

  ## RAG flow (inference)

  The generation pipeline ([`pipelines.inference.generate_content_pipeline`](pipelines/inference.py)) runs:

  1. **Intent extraction**: [`steps.rag.intent.extract_intent`](steps/rag/intent.py)
  2. **Query expansion**: [`steps.rag.query_expansion.expand_query`](steps/rag/query_expansion.py)
  3. **Retrieve chunks from Qdrant**: [`steps.rag.retrieval.retrieve_chunks`](steps/rag/retrieval.py)  
    - Uses embeddings from [`publish_assist.application.networks.embeddings.EmbeddingModelSingleton`](publish_assist/application/networks/embeddings.py)
  4. **Rerank**: [`steps.rag.rerank.rerank_chunks`](steps/rag/rerank.py)
  5. **Build compressed context**: [`steps.rag.context.build_context`](steps/rag/context.py)
  6. **Construct “original content” prompt**: [`steps.rag.prompt.build_prompt`](steps/rag/prompt.py)
  7. **LLM call**: [`steps.rag.llm.call_llm`](steps/rag/llm.py) using [`publish_assist.infra.llm.LlamaClient`](publish_assist/infra/llm.py)

  > The prompt explicitly instructs the model not to copy or closely paraphrase retrieved text (see [`steps.rag.prompt.build_prompt`](steps/rag/prompt.py)).

  ---

  ## Ingestion + feature engineering

  ### Ingestion (links → raw docs in Mongo)
  - Build links from sources (Substack RSS + YouTube via `yt-dlp`): [`api.services.integration_service.IntegrationService.build_links`](api/services/integration_service.py)
  - Crawl and store content:
    - Substack crawler: [`publish_assist.application.crawlers.substack.SubStackCrawler`](publish_assist/application/crawlers/substack.py)
    - YouTube crawler: [`publish_assist.application.crawlers.youtube.YoutubeCrawler`](publish_assist/application/crawlers/youtube.py)
    - ZenML step: [`steps.etl.crawl_links.crawl_links`](steps/etl/crawl_links.py)

  ### Feature engineering (raw docs → embedded chunks in Qdrant)
  Pipeline: [`pipelines.feature_engineering.feature_engineering`](pipelines/feature_engineering.py)

  - Fetch docs: [`steps.feature_engineering.query_data_warehouse.query_data_warehouse`](steps/feature_engineering/query_data_warehouse.py)
  - Clean: [`steps.feature_engineering.clean.clean_documents`](steps/feature_engineering/clean.py)
  - Chunk + embed: [`steps.feature_engineering.rag.chunk_and_embed`](steps/feature_engineering/rag.py)
    - Chunking utilities: [`publish_assist.application.preprocessing.operations.chunking.chunk_text`](publish_assist/application/preprocessing/operations/chunking.py)
  - Load to Qdrant: [`steps.feature_engineering.load_to_vector_db.load_to_vector_db`](steps/feature_engineering/load_to_vector_db.py)

  ---

  ## Evaluation (retrieval quality) (in progress)
  ---

  ## API (FastAPI)

  Base app: [`api.main.app`](api/main.py)

  Common endpoints:
  - `GET /v1/health` → [api/routes/health.py]
  - `POST /v1/ingest` → [api/routes/ingest.py]
  - `POST /v1/generate` → [api/routes/generate.py]
  - `GET /v1/jobs/{job_id}` → [api/routes/jobs.py]

  ---

  ## UI (Streamlit) (To be upgraded to react ts)

  Entry: [ui/app.py](ui/app.py)

  Flow:
  1. Identify user: [ui/pages/1_user.py](ui/pages/1_user.py)
  2. Ingest sources (Substack/YouTube): [ui/pages/2_ingest.py](ui/pages/2_ingest.py)
  3. Track progress: [ui/pages/3_job_status.py](ui/pages/3_job_status.py)
  4. Generate content: [ui/pages/4_generate.py](ui/pages/4_generate.py)

  The UI talks to the API via [ui/api_client.py](ui/api_client.py).

  ---

  ## Running locally

  ### Option A — Docker Compose (recommended)
  Use [docker-compose.yml](docker-compose.yml) to run the stack (API + dependencies).

  ```sh
  docker compose up -d --build
  ```

  Initialize Qdrant collections (once per fresh Qdrant):
  ```sh
  python scripts/init_qdrant.py --wait 60
  ```

  ### Option B — Run services manually
  Backend:
  ```sh
  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
  ```

  UI:
  ```sh
  streamlit run ui/app.py
  ```
  Will also need to provide qdrant and mongoDB refs.

  ---

  ## Configuration

  Settings are defined in [`publish_assist.settings.Settings`](publish_assist/settings.py) and loaded from `.env`.

  Common env vars:
  - `GROQ_API_KEY` (LLM calls) — used by [`publish_assist.infra.llm.LlamaClient`](publish_assist/infra/llm.py)
  - `DATABASE_HOST`, `DATABASE_NAME` (Mongo)
  - `QDRANT_URL` (cloud url if using that)
  - `TEXT_EMBEDDING_MODEL_ID` (default: `sentence-transformers`)
  - `RERANKING_CROSS_ENCODER_MODEL_ID`

  ---

  ## Deployment (EC2 + GitHub Actions)

  This repo includes an SSH-based deploy workflow: [.github/workflows/deploy-ec2.yml](.github/workflows/deploy-ec2.yml)

  On each push to `main`, it:
  - SSHes into the EC2 host
  - hard-resets to `origin/main`
  - restarts the stack via `docker compose up -d --build`

  Required GitHub secrets:
  - `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `EC2_APP_DIR`
  - `EC2_PORT` (optional)

  ---