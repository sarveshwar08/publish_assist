import feedparser
import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urlparse
from loguru import logger

from .base import BaseCrawler
from publish_assist.domain.documents import ArticleDocument, UserDocument

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n").strip()


def fetch_full_article_text(url: str) -> dict:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    title_tag = soup.find("meta", property="og:title")
    title = title_tag["content"].strip() if title_tag and title_tag.get("content") else soup.title.string.strip() if soup.title else "Substack Article"

    desc_tag = soup.find("meta", property="og:description")
    description = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""

    pub_tag = soup.find("meta", property="article:published_time")
    published = pub_tag["content"].strip() if pub_tag and pub_tag.get("content") else None

    article = soup.find("article")
    if article:
        content = article.get_text(separator="\n").strip()
    else:
        doc = Document(r.text)
        final_html = doc.summary(html_partial=True)
        final_soup = BeautifulSoup(final_html, "lxml")
        content = final_soup.get_text(separator="\n").strip()

    return {
        "url": url,
        "title": title,
        "description": description,
        "published": published,
        "content": content,
    }

class SubStackCrawler(BaseCrawler):
    model = ArticleDocument

    def extract(self, link: str, dataset_id: str, user: UserDocument):

        article_data = fetch_full_article_text(link)
        title = article_data["title"]
        description = article_data["description"]
        published = article_data["published"]
        raw_text = article_data["content"]

        content = {
            "Title": title,
            "Subtitle": description,
            "Content": raw_text,
            "Published": published,
        }

        instance = self.model(
            dataset_id=dataset_id,
            content=content,
            link=link,
            platform="substack",
            author_id=user.id,
            author_full_name=user.full_name,
        )
        try:
            instance.save()
            logger.info(f"Saved article: {title}")
        except Exception as e:
            logger.error(f"Failed to save article: {e}")

        logger.info(f"Finished scrapping custom article: {link}")