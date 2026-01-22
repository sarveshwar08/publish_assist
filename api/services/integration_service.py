from typing import Any, Dict, Optional, List
import feedparser
import subprocess

from zenml.client import Client

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

        medium = source_config.get("medium", {})
        if medium.get("enabled") and medium.get("username"):
            links.extend(self._medium_links(medium["username"], limit=limit))

        youtube = source_config.get("youtube", {})
        if youtube.get("enabled") and youtube.get("handle"):
            links.extend(self._youtube_links(youtube["handle"], limit=limit))

        # dedupe preserve order
        seen = set()
        unique = []
        for l in links:
            if l not in seen:
                seen.add(l)
                unique.append(l)

        return unique

    def start_ingestion_pipeline(
        self,
        source_config: Dict[str, Any],
        dataset_id: str,
        limit_per_source: int = 20,
    ) -> Dict[str, str]:
        
        links = self.build_links(source_config, limit=limit_per_source)
        if not links:
            raise ValueError("No links found from the given sources")

        from pipelines.digital_data_etl import digital_data_etl

        pipeline_run = digital_data_etl.with_options(
            run_name=f"ingest_{dataset_id}",
        )(
            links=links,
            dataset_id=dataset_id,
            source_config=source_config,
        )

        run_id = str(pipeline_run.id)

        run_url = None
        try:
            # ZenML dashboard URLs are not always configured in local setups.
            run_url = f"/zenml/runs/{run_id}"
        except Exception:
            pass

        return {"run_id": run_id, "run_url": run_url}

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        run = self.client.get_pipeline_run(run_id)

        status = str(run.status)  # may be enum

        step_statuses: Dict[str, str] = {}
        try:
            # step runs may exist depending on ZenML version
            step_runs = run.steps  # dict[name, step_run]
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
        if z in ("completed", "finished", "succeeded"):
            return "COMPLETED"
        if z in ("failed", "error"):
            return "FAILED"
        return "RUNNING"
