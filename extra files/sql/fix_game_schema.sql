-- HISTORICAL REPAIR ONLY. Already reflected in database/schema.sql.
-- Preserved original filename for the project work archive.
-- Do not rerun against the current database.
USE steamscope;

-- ============================================================
-- FIX: game table is missing 19 columns from the intended
-- schema (fike1.sql). Current table only has:
--   app_id, name, release_date, estimated_owners,
--   peak_ccu, required_age, price
-- This adds the rest, matching fike1.sql exactly, without
-- dropping/recreating the table (avoids FK complications with
-- any tables that already reference game(app_id)).
-- ============================================================

ALTER TABLE game
    ADD COLUMN discount_dlc_count INT UNSIGNED NULL AFTER price,
    ADD COLUMN description LONGTEXT NULL AFTER discount_dlc_count,
    ADD COLUMN header_image_url TEXT NULL AFTER description,
    ADD COLUMN website_url TEXT NULL AFTER header_image_url,
    ADD COLUMN support_url TEXT NULL AFTER website_url,
    ADD COLUMN support_email TEXT NULL AFTER support_url,
    ADD COLUMN metacritic_score INT UNSIGNED NULL AFTER support_email,
    ADD COLUMN metacritic_url TEXT NULL AFTER metacritic_score,
    ADD COLUMN user_score DECIMAL(5,2) NULL AFTER metacritic_url,
    ADD COLUMN positive_reviews INT UNSIGNED NULL AFTER user_score,
    ADD COLUMN negative_reviews INT UNSIGNED NULL AFTER positive_reviews,
    ADD COLUMN score_rank INT UNSIGNED NULL AFTER negative_reviews,
    ADD COLUMN achievement_count INT UNSIGNED NULL AFTER score_rank,
    ADD COLUMN recommendation_count INT UNSIGNED NULL AFTER achievement_count,
    ADD COLUMN notes LONGTEXT NULL AFTER recommendation_count,
    ADD COLUMN avg_playtime_forever INT UNSIGNED NULL AFTER notes,
    ADD COLUMN avg_playtime_2weeks INT UNSIGNED NULL AFTER avg_playtime_forever,
    ADD COLUMN median_playtime_forever INT UNSIGNED NULL AFTER avg_playtime_2weeks,
    ADD COLUMN median_playtime_2weeks INT UNSIGNED NULL AFTER median_playtime_forever;

-- Add the CHECK constraints from fike1.sql too, now that the
-- columns they reference exist.
ALTER TABLE game
    ADD CONSTRAINT chk_game_price
        CHECK (price IS NULL OR price >= 0),
    ADD CONSTRAINT chk_game_required_age
        CHECK (required_age IS NULL OR required_age >= 0),
    ADD CONSTRAINT chk_game_metacritic
        CHECK (metacritic_score IS NULL OR metacritic_score BETWEEN 0 AND 100),
    ADD CONSTRAINT chk_game_user_score
        CHECK (user_score IS NULL OR user_score >= 0);

-- Verify: should now show 26 columns total.
SHOW COLUMNS FROM game;
