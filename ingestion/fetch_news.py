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
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        pub_date_el = item.find("pubDate")

        articles.append(
            {
                "title": title_el.text.strip() if title_el is not None and title_el.text else None,
                "link": link_el.text.strip() if link_el is not None and link_el.text else None,
                "description": desc_el.text.strip() if desc_el is not None and desc_el.text else None,
                "pub_date": pub_date_el.text.strip() if pub_date_el is not None and pub_date_el.text else None,
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
