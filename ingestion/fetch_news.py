"""
fetch_news.py
-------------
Fetches the latest tech news articles from the Hacker News public RSS feed
using feedparser and returns them as a pandas DataFrame ready for downstream
processing and loading into Snowflake.
"""

import logging

import feedparser
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_FEED_URL = "https://hnrss.org/frontpage"
_HN_ITEM_URL = "https://news.ycombinator.com/item?id={}"


def fetch_news_as_dataframe(url: str | None = None) -> pd.DataFrame:
    """Fetch the RSS feed at *url* and return articles as a pandas DataFrame.

    Args:
        url: RSS feed URL to parse. Defaults to the Hacker News front page.

    Returns:
        DataFrame with columns TITLE, LINK, DESCRIPTION, PUB_DATE, SOURCE.
        PUB_DATE preserves the original RFC-2822 string from the feed so that
        Snowflake can parse it with TRY_TO_TIMESTAMP_NTZ.
    """
    feed_url = url or DEFAULT_FEED_URL
    logger.info("Fetching RSS feed from %s", feed_url)

    feed = feedparser.parse(feed_url)

    if feed.bozo:
        logger.warning(
            "feedparser reported a malformed feed (%s): %s",
            feed_url,
            feed.bozo_exception,
        )

    entries = feed.get("entries", [])
    logger.info("Parsed %d entries from feed", len(entries))

    rows = []
    for entry in entries:
        link = entry.get("link") or ""
        if not link:
            entry_id = entry.get("id", "")
            link = _HN_ITEM_URL.format(entry_id)
            logger.warning(
                "Entry '%s' has no <link>; using fallback URL %s",
                entry.get("title", "<no title>"),
                link,
            )

        rows.append(
            {
                "TITLE": entry.get("title"),
                "LINK": link,
                "DESCRIPTION": entry.get("summary"),
                "PUB_DATE": entry.get("published"),
                "SOURCE": "Hacker News RSS",
            }
        )

    return pd.DataFrame(rows, columns=["TITLE", "LINK", "DESCRIPTION", "PUB_DATE", "SOURCE"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    df = fetch_news_as_dataframe()
    print(f"Fetched {len(df)} articles.\n")
    print(df.head().to_string(index=False))
