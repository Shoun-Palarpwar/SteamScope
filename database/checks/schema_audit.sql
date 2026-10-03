USE steamscope;

-- ============================================================
-- FULL SCHEMA AUDIT
-- Dumps every table's actual live column list, in order, so it
-- can be compared with database/schema.sql. We found two tables
-- (game, achievement) where the live schema silently drifted
-- from the intended design -- this checks the other 22.
-- ============================================================

SELECT
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_KEY
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'steamscope'
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- Column count per table -- quick way to spot anything obviously short
SELECT
    TABLE_NAME,
    COUNT(*) AS column_count
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'steamscope'
GROUP BY TABLE_NAME
ORDER BY TABLE_NAME;
