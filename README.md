# tech-news-pipeline

A lightweight **ELT pipeline** that ingests the latest tech news from a public
RSS feed, stages the raw data in Snowflake, and exposes a clean analytics layer
via a SQL view — all orchestrated by Prefect.

---

## Architecture

```
┌─────────────────────┐     requests      ┌──────────────────┐
│  Hacker News RSS    │ ────────────────▶ │  fetch_news.py   │
│  (public API/feed)  │                   │  (Extract)       │
└─────────────────────┘                   └────────┬─────────┘
                                                   │ pandas DataFrame
                                                   ▼
                                          ┌──────────────────┐
                                          │ snowflake_       │
                                          │ connector.py     │
                                          │ (Load)           │
                                          └────────┬─────────┘
                                                   │ write_pandas
                                                   ▼
                                          ┌──────────────────┐
                                          │  Snowflake       │
                                          │  RAW_TECH_NEWS   │
                                          │  (staging table) │
                                          └────────┬─────────┘
                                                   │ SQL VIEW
                                                   ▼
                                          ┌──────────────────┐
                                          │  CLEAN_TECH_NEWS │
                                          │  (Transform)     │
                                          └──────────────────┘
```

All three steps are wired together by a **Prefect flow**
(`flows/news_pipeline_flow.py`).

---

## Project Structure

```
tech-news-pipeline/
├── ingestion/
│   └── fetch_news.py          # Extract: fetch & parse RSS feed
├── db/
│   └── snowflake_connector.py # Load: Snowflake connection + write helper
├── flows/
│   └── news_pipeline_flow.py  # Orchestrate with Prefect
├── requirements.txt
└── README.md
```

---

## ETL Process

### 1 · Extract — `ingestion/fetch_news.py`

Uses the **`requests`** library to pull the Hacker News front-page RSS feed
(`https://hnrss.org/frontpage`) and parses the XML with the Python standard
library.  The result is a **pandas DataFrame** with these columns:

| Column        | Description                         |
|---------------|-------------------------------------|
| `title`       | Article headline                    |
| `link`        | URL to the full article             |
| `description` | Short summary / excerpt             |
| `pub_date`    | Publication date (RFC-2822 string)  |
| `source`      | Feed identifier                     |

### 2 · Load — `db/snowflake_connector.py`

Uses **`snowflake-connector-python`** to:

* Open an authenticated connection (credentials via environment variables).
* Write the DataFrame to the `RAW_TECH_NEWS` staging table with
  `snowflake.connector.pandas_tools.write_pandas`.

### 3 · Transform — SQL inside Snowflake

A `CREATE OR REPLACE VIEW` statement creates `CLEAN_TECH_NEWS` which:

* Parses the `pub_date` string into a proper `TIMESTAMP_NTZ`.
* Trims whitespace from the description.
* Filters out rows where `title` or `link` is `NULL`.

---

## Environment Variables

| Variable              | Required | Description                         |
|-----------------------|----------|-------------------------------------|
| `SNOWFLAKE_ACCOUNT`   | ✅       | e.g. `xy12345.us-east-1`            |
| `SNOWFLAKE_USER`      | ✅       | Snowflake username                  |
| `SNOWFLAKE_PASSWORD`  | ✅       | Snowflake password                  |
| `SNOWFLAKE_DATABASE`  | ✅       | Target database                     |
| `SNOWFLAKE_WAREHOUSE` | ✅       | Virtual warehouse                   |
| `SNOWFLAKE_SCHEMA`    | ❌       | Schema (default: `PUBLIC`)          |
| `SNOWFLAKE_ROLE`      | ❌       | Role to assume                      |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set Snowflake credentials
export SNOWFLAKE_ACCOUNT=xy12345.us-east-1
export SNOWFLAKE_USER=my_user
export SNOWFLAKE_PASSWORD=my_password
export SNOWFLAKE_DATABASE=my_db
export SNOWFLAKE_WAREHOUSE=my_wh

# 3. Run the pipeline once
python flows/news_pipeline_flow.py
```

---

## Running with Prefect

```bash
# Start the Prefect server (optional, for UI)
prefect server start

# Deploy and run the flow
prefect deploy flows/news_pipeline_flow.py:tech_news_pipeline
prefect run deployment tech-news-pipeline/tech_news_pipeline
```

---

## Dependencies

| Package                      | Purpose                              |
|------------------------------|--------------------------------------|
| `requests`                   | HTTP client for RSS feed fetching    |
| `pandas`                     | In-memory data manipulation          |
| `snowflake-connector-python` | Snowflake connection & data loading  |
| `prefect`                    | Workflow orchestration               |
| `streamlit`                  | Interactive data dashboard (future)  |