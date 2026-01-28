from typing import Any, Dict

from zenml.client import Client

from pipelines.inference import generate_content_pipeline


class GenerateService:

    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is None:
            self._client = Client()
        return self._client

    def start_generation_pipeline(
        self,
        *,
        dataset_id: str,
        topic: str,
        platform: str,
        tone: str,
        use_web: bool = False,
    ) -> Dict[str, Any]:
        pipeline_run = generate_content_pipeline.with_options(
            run_name=f"generate_{dataset_id}",
        )(
            dataset_id=dataset_id,
            topic=topic,
            platform=platform,
            tone=tone,
            use_web=use_web,
        )

        if pipeline_run is None:
            raise RuntimeError("Pipeline did not start (got None PipelineRunResponse).")

        run_id = str(pipeline_run.id)
        run_url = f"/zenml/runs/{run_id}"

        return {"run_id": run_id, "run_url": run_url}

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        client = self._get_client()
        run = client.get_pipeline_run(run_id)

        status = str(run.status)
        steps: Dict[str, str] = {}
        try:
            for name, step_run in run.steps.items():
                steps[name] = str(step_run.status)
        except Exception:
            pass

        return {"status": status, "steps": steps}

    def load_generated_output(self, run_id: str) -> str:

        client = self._get_client()
        run = client.get_pipeline_run(run_id)

        steps = getattr(run, "steps", {}) or {}
        if not isinstance(steps, dict) or not steps:
            raise RuntimeError("Run has no steps to inspect for outputs.")

        # change here too, if we ever change step name
        step_run = steps.get("call_llm")
        if step_run is None: #accomodate zenml behaviour
            for name, sr in steps.items():
                if str(name).endswith("call_llm"):
                    step_run = sr
                    break

        if step_run is None:
            raise RuntimeError("Could not find `call_llm` step in run.")
            
        artifact = getattr(step_run, "output", None)

        if artifact is None:
            raise RuntimeError("No output artifact found on `call_llm` step.")

        if hasattr(artifact, "load") and callable(getattr(artifact, "load")):
            value = artifact.load()
        elif hasattr(artifact, "id"):
            av = client.get_artifact_version(artifact.id)
            value = av.load()
        else:
            raise RuntimeError("Unsupported artifact type, cannot load output.")

        if isinstance(value, str):
            return value

        return str(value)
