import re
import requests
from bs4 import BeautifulSoup
from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi

from .base import BaseCrawler
from publish_assist.domain.documents import YoutubeDocument, UserDocument


class YoutubeCrawler(BaseCrawler):
    model = YoutubeDocument
    
    @staticmethod
    def extract_video_id(url: str) -> str:
        patterns = [
            r"v=([A-Za-z0-9_-]{11})",
            r"youtu\.be/([A-Za-z0-9_-]{11})"
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        raise ValueError(f"Cannot extract video id from: {url}")

    @staticmethod
    def fetch_transcript(video_id: str, languages=("en", "en-US")) -> str:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=list(languages))
            text = " ".join([t["text"] for t in transcript])
            return text
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {e}")
            return ""

    @staticmethod
    def fetch_video_metadata(url: str) -> tuple[str, str]:
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            title_tag = soup.find("meta", property="og:title")
            title = title_tag["content"] if title_tag else "Unknown Title"

            desc_tag = soup.find("meta", property="og:description")
            description = desc_tag["content"] if desc_tag else ""

            return title, description
        except Exception as e:
            logger.warning(f"Could not fetch metadata for {url}: {e}")
            return "Unknown Title", ""

    def extract(self, link: str, user: UserDocument):
        video_id = YoutubeCrawler.extract_video_id(link)
        raw_text = YoutubeCrawler.fetch_transcript(video_id)
        title, description = YoutubeCrawler.fetch_video_metadata(link)

        content = {
            "Title": title,
            "Subtitle": description,
            "Content": raw_text,
        }

        instance = self.model(
            content=content,
            link=link,
            platform="youtube",
            author_id=user.id,
            author_full_name=user.full_name,
        )
        instance.save()

        logger.info(f"Finished scrapping youtube video: {link}")
