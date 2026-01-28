from datetime import datetime
from typing import Iterable
import time

from loguru import logger
from pymongo.collection import Collection

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from .base import SingletonMeta
from publish_assist.settings import settings

class YouTubeTranscriptClient(metaclass=SingletonMeta):
    def __init__(
        self,
        transcripts_collection: Collection,
        proxy_config= None,
    ):
        self._api = YouTubeTranscriptApi(proxy_config=WebshareProxyConfig(
        proxy_username=settings.WEBSHARE_USERNAME,
        proxy_password=settings.WEBSHARE_PASSWORD,
    ))
        self._collection = transcripts_collection

    def get_transcript_text(
        self,
        video_id: str,
        languages: Iterable[str] = ("en",),
    ) -> str:
        cached = self._collection.find_one({"_id": video_id})
        if cached:
            logger.debug(f"YT transcript cache hit for {video_id}")
            return cached["text"]

        #TODO: P2 - use a better way to rate limit.
        time.sleep(0.7)
        logger.info(f"Fetching YT transcript for {video_id}")

        fetched = self._api.fetch(video_id, languages=languages).snippets

        text = " ".join(seg.text for seg in fetched)

        self._collection.insert_one({
            "_id": video_id,
            "video_id": video_id,
            "text": text,
            "language": languages[0],
            "fetched_at": datetime.utcnow(),
        })

        return text
