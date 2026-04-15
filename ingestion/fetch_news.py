"""
fetch_news.py
-------------
Fetches the latest tech news articles from the Hacker News public RSS feed
and returns them as a list of dictionaries ready for downstream processing.
"""

import xml.etree.ElementTree as ET

import pandas as pd
import requests

RSS_FEED_URL = "https://hnrss.org/frontpage"


def fetch_rss_feed(url: str = RSS_FEED_URL, timeout: int = 30) -> str:
    """Fetch the raw RSS/XML content from *url*.

    Args:
        url: The RSS feed URL to request.
        timeout: Request timeout in seconds.

    Returns:
        Raw XML string response body.

    Raises:
        requests.HTTPError: If the server returns a 4xx/5xx status code.
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def _element_text(element: ET.Element | None) -> str | None:
    """Return stripped text content of *element*, or ``None`` if absent."""
    if element is None or not element.text:
        return None
    return element.text.strip()


def parse_rss(xml_text: str) -> list[dict]:
    """Parse an RSS XML string into a list of article dictionaries.

    Args:
        xml_text: Raw RSS XML string.

    Returns:
        List of dicts with keys: title, link, description, pub_date, source.
    """
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    articles = []
    for item in channel.findall("item"):
        articles.append(
            {
                "title": _element_text(item.find("title")),
                "link": _element_text(item.find("link")),
                "description": _element_text(item.find("description")),
                "pub_date": _element_text(item.find("pubDate")),
                "source": "Hacker News RSS",
            }
        )
    return articles


def fetch_news_as_dataframe(url: str = RSS_FEED_URL) -> pd.DataFrame:
    """End-to-end helper: fetch the RSS feed and return a pandas DataFrame.

    Args:
        url: The RSS feed URL to request.

    Returns:
        DataFrame with columns: title, link, description, pub_date, source.
    """
    xml_text = fetch_rss_feed(url)
    articles = parse_rss(xml_text)
    return pd.DataFrame(articles)


if __name__ == "__main__":
    df = fetch_news_as_dataframe()
    print(f"Fetched {len(df)} articles.")
    print(df[["title", "pub_date"]].head(10).to_string(index=False))
