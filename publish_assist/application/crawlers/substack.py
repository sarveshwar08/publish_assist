import feedparser
import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urlparse
from loguru import logger

from .base import BaseCrawler
from publish_assist.domain.documents import SubstackDocument, UserDocument

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n").strip()

def fetch_full_article_text(url: str) -> str:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    article = soup.find("article")
    if article:
        return article.get_text(separator="\n").strip()

    # if no article tag found
    doc = Document(r.text)
    final_html = doc.summary(html_partial=True)
    final_soup = BeautifulSoup(final_html, "lxml")
    
    return final_soup.get_text(separator="\n").strip()

class SubStackCrawler(BaseCrawler):
    model = SubstackDocument

    def extract(self, link: str, user: UserDocument):
        feed = feedparser.parse(link)

        for entry in feed.entries:
            url = entry.link
            title = entry.title
            description = entry.get("description", None)
            published = entry.get("published", None)

            raw_text = fetch_full_article_text(url)
            
            content = {
                "Title": title,
                "Subtitle": description,
                "Content": raw_text,
                "Published": published,
            }
            
            instance = self.model(
                content=content,
                link=link,
                platform="substack",
                author_id=user.id,
                author_full_name=user.full_name,
            )
            instance.save()

        logger.info(f"Finished scrapping custom article: {link}")