"""
snowflake_connector.py
----------------------
Provides a thin wrapper around snowflake-connector-python to create and
manage a Snowflake connection using environment variables for credentials.

Required environment variables
-------------------------------
SNOWFLAKE_ACCOUNT   - e.g. "xy12345.us-east-1"
SNOWFLAKE_USER      - Snowflake username
SNOWFLAKE_PASSWORD  - Snowflake password
SNOWFLAKE_DATABASE  - Target database
SNOWFLAKE_SCHEMA    - Target schema  (default: PUBLIC)
SNOWFLAKE_WAREHOUSE - Virtual warehouse to use
SNOWFLAKE_ROLE      - Role to assume (optional)
"""

import os

import snowflake.connector
from snowflake.connector import SnowflakeConnection


def get_snowflake_connection() -> SnowflakeConnection:
    """Create and return an authenticated Snowflake connection.

    Credentials are read exclusively from environment variables so that no
    secrets are hard-coded in the source.

    Returns:
        An open :class:`snowflake.connector.SnowflakeConnection` instance.

    Raises:
        KeyError: If a required environment variable is missing.
        snowflake.connector.errors.DatabaseError: On authentication failure.
    """
    connect_kwargs = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PASSWORD"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC"),
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
    }

    role = os.environ.get("SNOWFLAKE_ROLE")
    if role:
        connect_kwargs["role"] = role

    return snowflake.connector.connect(**connect_kwargs)


def load_dataframe_to_snowflake(
    df,
    table_name: str,
    conn: SnowflakeConnection | None = None,
    *,
    auto_create_table: bool = True,
    overwrite: bool = False,
) -> None:
    """Write a pandas DataFrame to a Snowflake table using write_pandas.

    Args:
        df: pandas DataFrame to upload.
        table_name: Destination table name (case-insensitive in Snowflake).
        conn: Optional existing connection. A new one is opened if not provided.
        auto_create_table: When ``True`` the table is created if it doesn't
            exist (uses ``write_pandas`` with ``auto_create_table=True``).
        overwrite: When ``True`` the existing table data is replaced.
    """
    from snowflake.connector.pandas_tools import write_pandas

    close_conn = conn is None
    if conn is None:
        conn = get_snowflake_connection()

    try:
        write_pandas(
            conn,
            df,
            table_name=table_name.upper(),
            auto_create_table=auto_create_table,
            overwrite=overwrite,
        )
    finally:
        if close_conn:
            conn.close()
