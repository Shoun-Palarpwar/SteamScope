USE steamscope;

-- ============================================================
-- STEAMSCOPE DB DIAGNOSTIC
-- Run this end-to-end and read the output top to bottom.
-- Goal: find out exactly what's populated, empty, or dangling
-- in the current database. All statements below are read-only.
-- ============================================================

-- ------------------------------------------------------------
-- 1. ROW COUNTS — every table in one shot
-- ------------------------------------------------------------
SELECT 'user'            AS table_name, COUNT(*) AS row_count FROM `user`
UNION ALL SELECT 'game',              COUNT(*) FROM `game`
UNION ALL SELECT 'developer',         COUNT(*) FROM `developer`
UNION ALL SELECT 'publisher',         COUNT(*) FROM `publisher`
UNION ALL SELECT 'genre',             COUNT(*) FROM `genre`
UNION ALL SELECT 'tag',               COUNT(*) FROM `tag`
UNION ALL SELECT 'category',          COUNT(*) FROM `category`
UNION ALL SELECT 'platform',          COUNT(*) FROM `platform`
UNION ALL SELECT 'language',          COUNT(*) FROM `language`
UNION ALL SELECT 'game_developer',    COUNT(*) FROM `game_developer`
UNION ALL SELECT 'game_publisher',    COUNT(*) FROM `game_publisher`
UNION ALL SELECT 'game_genre',        COUNT(*) FROM `game_genre`
UNION ALL SELECT 'game_tag',          COUNT(*) FROM `game_tag`
UNION ALL SELECT 'game_category',     COUNT(*) FROM `game_category`
UNION ALL SELECT 'game_platform',     COUNT(*) FROM `game_platform`
UNION ALL SELECT 'game_language',     COUNT(*) FROM `game_language`
UNION ALL SELECT 'game_screenshot',   COUNT(*) FROM `game_screenshot`
UNION ALL SELECT 'review',            COUNT(*) FROM `review`
UNION ALL SELECT 'achievement',       COUNT(*) FROM `achievement`
UNION ALL SELECT 'user_achievement',  COUNT(*) FROM `user_achievement`
UNION ALL SELECT 'library',           COUNT(*) FROM `library`
UNION ALL SELECT 'wishlist',          COUNT(*) FROM `wishlist`
UNION ALL SELECT 'purchase',          COUNT(*) FROM `purchase`
UNION ALL SELECT 'user_activity',     COUNT(*) FROM `user_activity`;

-- ------------------------------------------------------------
-- 2. DANGLING JUNCTION ROWS
-- Rows in a bridge table whose referenced lookup row no longer
-- exists (expected to be non-zero right now, since fike4.sql
-- deleted developer/publisher/genre/tag/category/platform but
-- FK constraints should have cascaded... this confirms whether
-- they actually did, or whether junction rows survived orphaned).
-- ------------------------------------------------------------
SELECT 'game_developer -> developer' AS check_name, COUNT(*) AS orphan_rows
FROM `game_developer` gd
LEFT JOIN `developer` d ON gd.developer_id = d.developer_id
WHERE d.developer_id IS NULL

UNION ALL
SELECT 'game_publisher -> publisher', COUNT(*)
FROM `game_publisher` gp
LEFT JOIN `publisher` p ON gp.publisher_id = p.publisher_id
WHERE p.publisher_id IS NULL

UNION ALL
SELECT 'game_genre -> genre', COUNT(*)
FROM `game_genre` gg
LEFT JOIN `genre` g ON gg.genre_id = g.genre_id
WHERE g.genre_id IS NULL

UNION ALL
SELECT 'game_tag -> tag', COUNT(*)
FROM `game_tag` gt
LEFT JOIN `tag` t ON gt.tag_id = t.tag_id
WHERE t.tag_id IS NULL

UNION ALL
SELECT 'game_category -> category', COUNT(*)
FROM `game_category` gc
LEFT JOIN `category` c ON gc.category_id = c.category_id
WHERE c.category_id IS NULL

UNION ALL
SELECT 'game_platform -> platform', COUNT(*)
FROM `game_platform` gpl
LEFT JOIN `platform` pl ON gpl.platform_id = pl.platform_id
WHERE pl.platform_id IS NULL;

-- ------------------------------------------------------------
-- 3. GAME TABLE HEALTH
-- ------------------------------------------------------------
SELECT
    COUNT(*)                    AS total_games,
    COUNT(DISTINCT app_id)      AS unique_app_ids,
    SUM(name IS NULL)           AS null_names,
    SUM(release_date IS NULL)   AS null_release_dates,
    SUM(price IS NULL)          AS null_prices
FROM game;

-- ------------------------------------------------------------
-- 4. REVIEW -> GAME FK COVERAGE
-- ------------------------------------------------------------
SELECT
    COUNT(*) AS total_reviews,
    SUM(g.app_id IS NULL) AS reviews_with_no_matching_game
FROM review r
LEFT JOIN game g ON r.app_id = g.app_id;

-- ------------------------------------------------------------
-- 5. FULL FOREIGN KEY MAP (sanity check schema itself)
-- ------------------------------------------------------------
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'steamscope'
  AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME, COLUMN_NAME;
