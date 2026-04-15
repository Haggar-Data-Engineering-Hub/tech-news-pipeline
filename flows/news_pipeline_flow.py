"""
news_pipeline_flow.py
---------------------
Prefect flow that orchestrates the full tech-news ETL pipeline:

    Extract  →  fetch latest articles from the Hacker News RSS feed
    Load     →  write raw articles to a Snowflake staging table
    Transform→  run a SQL view / query inside Snowflake to produce the
                clean analytics layer

Run locally:
    python flows/news_pipeline_flow.py
"""

import pandas as pd
from prefect import flow, get_run_logger, task

from db.snowflake_connector import get_snowflake_connection, load_dataframe_to_snowflake
from ingestion.fetch_news import fetch_news_as_dataframe

# ---------------------------------------------------------------------------
# Configuration – adjust as needed or drive via Prefect variables / env vars
# ---------------------------------------------------------------------------
RAW_TABLE = "RAW_TECH_NEWS"
CLEAN_VIEW = "CLEAN_TECH_NEWS"

TRANSFORM_SQL = f"""
CREATE OR REPLACE VIEW {CLEAN_VIEW} AS
SELECT
    TITLE,
    LINK,
    -- Strip leading/trailing whitespace from description
    TRIM(DESCRIPTION)          AS DESCRIPTION,
    -- Parse the RFC-2822 pub_date into a proper TIMESTAMP
    TRY_TO_TIMESTAMP_NTZ(PUB_DATE, 'DY, DD MON YYYY HH24:MI:SS TZH') AS PUBLISHED_AT,
    SOURCE,
    CURRENT_TIMESTAMP()        AS LOADED_AT
FROM {RAW_TABLE}
WHERE TITLE IS NOT NULL
  AND LINK  IS NOT NULL;
"""


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@task(name="extract-tech-news", retries=3, retry_delay_seconds=10)
def extract(feed_url: str | None = None) -> pd.DataFrame:
    """Fetch articles from the RSS feed and return a DataFrame."""
    logger = get_run_logger()
    kwargs = {"url": feed_url} if feed_url else {}
    df = fetch_news_as_dataframe(**kwargs)
    logger.info("Extracted %d articles from RSS feed.", len(df))
    return df


@task(name="load-to-snowflake")
def load(df: pd.DataFrame, table_name: str = RAW_TABLE, overwrite: bool = True) -> None:
    """Load the DataFrame into a Snowflake raw/staging table."""
    logger = get_run_logger()
    if df.empty:
        logger.warning("DataFrame is empty – skipping Snowflake load.")
        return
    load_dataframe_to_snowflake(df, table_name=table_name, overwrite=overwrite)
    logger.info("Loaded %d rows into Snowflake table '%s'.", len(df), table_name)


@task(name="transform-in-snowflake")
def transform() -> None:
    """Create/replace the clean analytics view inside Snowflake."""
    logger = get_run_logger()
    conn = get_snowflake_connection()
    try:
        conn.cursor().execute(TRANSFORM_SQL)
        logger.info("Transformation view '%s' created/updated successfully.", CLEAN_VIEW)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


@flow(name="tech-news-pipeline", log_prints=True)
def tech_news_pipeline(feed_url: str | None = None, overwrite: bool = True) -> None:
    """End-to-end tech news ETL pipeline.

    Args:
        feed_url: Override the default RSS feed URL (useful for testing).
        overwrite: Whether to replace the raw Snowflake table on each run.
    """
    df = extract(feed_url=feed_url)
    load(df, overwrite=overwrite)
    transform()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tech_news_pipeline()
