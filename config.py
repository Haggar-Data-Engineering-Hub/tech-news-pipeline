"""
config.py
---------
Centralise les constantes de configuration du pipeline :
noms de tables, de vues et requêtes SQL de transformation.
"""

RAW_TABLE = "RAW_TECH_NEWS"
CLEAN_VIEW = "CLEAN_TECH_NEWS"

TRANSFORM_SQL = f"""
CREATE OR REPLACE VIEW {CLEAN_VIEW} AS
SELECT
    TITLE,
    LINK,
    TRIM(DESCRIPTION)          AS DESCRIPTION,
    TRY_TO_TIMESTAMP_NTZ(PUB_DATE, 'DY, DD MON YYYY HH24:MI:SS TZH') AS PUBLISHED_AT,
    SOURCE,
    CURRENT_TIMESTAMP()        AS LOADED_AT
FROM {RAW_TABLE}
WHERE TITLE IS NOT NULL
  AND LINK  IS NOT NULL;
"""
