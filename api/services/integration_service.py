#bridge between zenml pipeline invocation and api

from typing import Any, Dict, Optional, List
import feedparser
import subprocess

from zenml.client import Client
from pipelines.digital_data_etl import digital_data_etl
from pipelines.feature_engineering import feature_engineering as feature_engineering_pipeline

class IntegrationService:

    def __init__(self):
        self.client = Client()

    def _substack_links(self, username: str, limit: int = 20) -> List[str]:
        rss_url = f"https://{username}.substack.com/feed"
        feed = feedparser.parse(rss_url)
        links = []
        for e in feed.entries[:limit]:
            if "link" in e:
                links.append(e.link)
        return links
    
    def _youtube_links(self, handle: str, limit: int = 20) -> List[str]:

        if not handle.startswith("@"):
            handle = "@" + handle

        channel_url = f"https://www.youtube.com/{handle}/videos"

        try:
            cmd = ["yt-dlp", "--flat-playlist", "--print", "url", channel_url]
            out = subprocess.check_output(cmd, text=True).strip().splitlines()
            urls = []
            for u in out[:limit]:
                if u.startswith("http"):
                    urls.append(u)
                else:
                    urls.append(f"https://www.youtube.com{u}")
            return urls
        except Exception:
            return []
        
    def build_links(self, source_config: Dict[str, Any], limit: int = 20) -> List[str]:
        links: List[str] = []

        substack = source_config.get("substack", {})
        if substack.get("enabled") and substack.get("username"):
            links.extend(self._substack_links(substack["username"], limit=limit))

        youtube = source_config.get("youtube", {})
        if youtube.get("enabled") and youtube.get("handle"):
            links.extend(self._youtube_links(youtube["handle"], limit=limit))

        #dedup
        return list(dict.fromkeys(links))

    def start_ingestion_pipeline(
        self,
        source_config: Dict[str, Any],
        dataset_id: str,
        limit_per_source: int = 25,
        user_full_name: str = None,
    ) -> Dict[str, str]:
        
        links = self.build_links(source_config, limit=limit_per_source)
        if not links:
            raise ValueError("No links found from the given sources")

        pipeline_run = digital_data_etl.with_options(
            run_name=f"ingest_{dataset_id}",
        )(
            user_full_name=user_full_name,
            links=links,
            dataset_id=dataset_id,
        )

        run_id = str(pipeline_run.id)

        run_url = None
        try:
            run_url = f"/zenml/runs/{run_id}"
        except Exception:
            pass

        return {"run_id": run_id, "run_url": run_url, "links_found": len(links)}

    def start_feature_engineering_pipeline(
        self,
        *,
        dataset_id: str,
        wait_for: str | list[str] | None = None,
    ) -> Dict[str, str]:
        pipeline_run = feature_engineering_pipeline.with_options(
            run_name=f"feature_engg_{dataset_id}",
        )(
            dataset_id=dataset_id,
            wait_for=wait_for,
        )

        run_id = str(pipeline_run.id)

        run_url = None
        try:
            run_url = f"/zenml/runs/{run_id}"
        except Exception:
            pass

        return {"run_id": run_id, "run_url": run_url}

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        run = self.client.get_pipeline_run(run_id) #PipelineRunResponse object

        status = str(run.status)

        step_statuses: Dict[str, str] = {}
        try:
            step_runs = run.steps  # {[name, step_run]}
            for step_name, step_run in step_runs.items():
                step_statuses[step_name] = str(step_run.status)
        except Exception:
            pass

        return {
            "status": status,
            "steps": step_statuses,
        }


    def normalize_status(self, zenml_status: str) -> str:
        z = zenml_status.lower()
        if z in ("running", "initializing"):
            return "RUNNING"
        if z in ("completed", "finished", "succeeded", "cached"):
            return "COMPLETED"
        if z in ("failed", "error"):
            return "FAILED"
        return "RUNNING"
