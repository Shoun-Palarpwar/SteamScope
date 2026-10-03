-- Recovered from the complete text captured before the cleanup.
-- Historical inspection queries; retained for reference.
USE steamscope;

SELECT COUNT(*) AS total_games FROM game;

SELECT *
FROM game
LIMIT 10;
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT app_id) AS unique_app_ids,
    COUNT(name) AS non_null_names
FROM game;
