-- HISTORICAL DESIGN ONLY. For fresh setup use database/schema.sql instead.
-- Preserved original filename for the project work archive.
CREATE DATABASE IF NOT EXISTS steamscope
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
    

USE steamscope;
USE steamscope;

-- =========================================================
-- STEAMSCOPE DATABASE SCHEMA
-- MySQL 8.0.46
-- =========================================================

-- =========================================================
-- 1. USER
-- =========================================================
CREATE TABLE user (
    user_id BIGINT UNSIGNED AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),
    UNIQUE KEY uq_user_username (username),
    UNIQUE KEY uq_user_email (email)
) ENGINE=InnoDB;


-- =========================================================
-- 2. GAME
-- =========================================================
CREATE TABLE game (
    app_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    release_date DATE NULL,
    estimated_owners VARCHAR(50) NULL,
    peak_ccu INT UNSIGNED NULL,
    required_age INT UNSIGNED NULL,
    price DECIMAL(10,2) NULL,
    discount_dlc_count INT UNSIGNED NULL,
    description TEXT NULL,

    header_image_url TEXT NULL,
    website_url TEXT NULL,
    support_url TEXT NULL,
    support_email VARCHAR(255) NULL,

    metacritic_score INT UNSIGNED NULL,
    metacritic_url TEXT NULL,
    user_score DECIMAL(5,2) NULL,

    positive_reviews INT UNSIGNED NULL,
    negative_reviews INT UNSIGNED NULL,
    score_rank INT UNSIGNED NULL,

    achievement_count INT UNSIGNED NULL,
    recommendation_count INT UNSIGNED NULL,

    notes TEXT NULL,

    avg_playtime_forever INT UNSIGNED NULL,
    avg_playtime_2weeks INT UNSIGNED NULL,
    median_playtime_forever INT UNSIGNED NULL,
    median_playtime_2weeks INT UNSIGNED NULL,

    PRIMARY KEY (app_id),

    CONSTRAINT chk_game_price
        CHECK (price IS NULL OR price >= 0),

    CONSTRAINT chk_game_required_age
        CHECK (required_age IS NULL OR required_age >= 0),

    CONSTRAINT chk_game_metacritic
        CHECK (metacritic_score IS NULL OR metacritic_score BETWEEN 0 AND 100),

    CONSTRAINT chk_game_user_score
        CHECK (user_score IS NULL OR user_score >= 0)
) ENGINE=InnoDB;


-- =========================================================
-- 3. DEVELOPER
-- =========================================================
CREATE TABLE developer (
    developer_id INT UNSIGNED AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,

    PRIMARY KEY (developer_id),
    UNIQUE KEY uq_developer_name (name)
) ENGINE=InnoDB;


-- =========================================================
-- 4. PUBLISHER
-- =========================================================
CREATE TABLE publisher (
    publisher_id INT UNSIGNED AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,

    PRIMARY KEY (publisher_id),
    UNIQUE KEY uq_publisher_name (name)
) ENGINE=InnoDB;


-- =========================================================
-- 5. GENRE
-- =========================================================
CREATE TABLE genre (
    genre_id INT UNSIGNED AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,

    PRIMARY KEY (genre_id),
    UNIQUE KEY uq_genre_name (name)
) ENGINE=InnoDB;


-- =========================================================
-- 6. TAG
-- =========================================================
CREATE TABLE tag (
    tag_id INT UNSIGNED AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,

    PRIMARY KEY (tag_id),
    UNIQUE KEY uq_tag_name (name)
) ENGINE=InnoDB;


-- =========================================================
-- 7. CATEGORY
-- =========================================================
CREATE TABLE category (
    category_id INT UNSIGNED AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,

    PRIMARY KEY (category_id),
    UNIQUE KEY uq_category_name (name)
) ENGINE=InnoDB;


-- =========================================================
-- 8. PLATFORM
-- =========================================================
CREATE TABLE platform (
    platform_id INT UNSIGNED AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,

    PRIMARY KEY (platform_id),
    UNIQUE KEY uq_platform_name (name)
) ENGINE=InnoDB;


-- =========================================================
-- 9. LANGUAGE
-- =========================================================
CREATE TABLE language (
    language_id INT UNSIGNED AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,

    PRIMARY KEY (language_id),
    UNIQUE KEY uq_language_name (name)
) ENGINE=InnoDB;


-- =========================================================
-- 10. GAME_DEVELOPER
-- =========================================================
CREATE TABLE game_developer (
    app_id BIGINT UNSIGNED NOT NULL,
    developer_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (app_id, developer_id),

    CONSTRAINT fk_game_developer_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_game_developer_developer
        FOREIGN KEY (developer_id)
        REFERENCES developer(developer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 11. GAME_PUBLISHER
-- =========================================================
CREATE TABLE game_publisher (
    app_id BIGINT UNSIGNED NOT NULL,
    publisher_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (app_id, publisher_id),

    CONSTRAINT fk_game_publisher_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_game_publisher_publisher
        FOREIGN KEY (publisher_id)
        REFERENCES publisher(publisher_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 12. GAME_GENRE
-- =========================================================
CREATE TABLE game_genre (
    app_id BIGINT UNSIGNED NOT NULL,
    genre_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (app_id, genre_id),

    CONSTRAINT fk_game_genre_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_game_genre_genre
        FOREIGN KEY (genre_id)
        REFERENCES genre(genre_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 13. GAME_TAG
-- =========================================================
CREATE TABLE game_tag (
    app_id BIGINT UNSIGNED NOT NULL,
    tag_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (app_id, tag_id),

    CONSTRAINT fk_game_tag_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_game_tag_tag
        FOREIGN KEY (tag_id)
        REFERENCES tag(tag_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 14. GAME_CATEGORY
-- =========================================================
CREATE TABLE game_category (
    app_id BIGINT UNSIGNED NOT NULL,
    category_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (app_id, category_id),

    CONSTRAINT fk_game_category_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_game_category_category
        FOREIGN KEY (category_id)
        REFERENCES category(category_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 15. GAME_PLATFORM
-- =========================================================
CREATE TABLE game_platform (
    app_id BIGINT UNSIGNED NOT NULL,
    platform_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (app_id, platform_id),

    CONSTRAINT fk_game_platform_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_game_platform_platform
        FOREIGN KEY (platform_id)
        REFERENCES platform(platform_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 16. GAME_LANGUAGE
-- =========================================================
CREATE TABLE game_language (
    app_id BIGINT UNSIGNED NOT NULL,
    language_id INT UNSIGNED NOT NULL,
    support_type ENUM('SUPPORTED', 'FULL_AUDIO') NOT NULL,

    PRIMARY KEY (app_id, language_id, support_type),

    CONSTRAINT fk_game_language_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_game_language_language
        FOREIGN KEY (language_id)
        REFERENCES language(language_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 17. GAME_SCREENSHOT
-- =========================================================
CREATE TABLE game_screenshot (
    screenshot_id BIGINT UNSIGNED AUTO_INCREMENT,
    app_id BIGINT UNSIGNED NOT NULL,
    screenshot_url TEXT NOT NULL,

    PRIMARY KEY (screenshot_id),

    CONSTRAINT fk_game_screenshot_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 18. REVIEW
-- =========================================================
CREATE TABLE review (
    review_id BIGINT UNSIGNED AUTO_INCREMENT,
    steamid BIGINT UNSIGNED NOT NULL,
    app_id BIGINT UNSIGNED NOT NULL,

    voted_up BOOLEAN NOT NULL,
    votes_up INT UNSIGNED DEFAULT 0,
    votes_funny INT UNSIGNED DEFAULT 0,
    weighted_vote_score DECIMAL(10,8) NULL,

    playtime_forever INT UNSIGNED NULL,
    playtime_at_review INT UNSIGNED NULL,
    num_games_owned INT UNSIGNED NULL,
    num_reviews INT UNSIGNED NULL,

    review_text TEXT NULL,

    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    PRIMARY KEY (review_id),

    CONSTRAINT fk_review_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT chk_review_weighted_score
        CHECK (
            weighted_vote_score IS NULL
            OR weighted_vote_score >= 0
        )
) ENGINE=InnoDB;


-- =========================================================
-- 19. ACHIEVEMENT
-- =========================================================
CREATE TABLE achievement (
    achievement_id BIGINT UNSIGNED AUTO_INCREMENT,
    app_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,

    PRIMARY KEY (achievement_id),

    CONSTRAINT fk_achievement_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 20. USER_ACHIEVEMENT
-- =========================================================
CREATE TABLE user_achievement (
    user_id BIGINT UNSIGNED NOT NULL,
    achievement_id BIGINT UNSIGNED NOT NULL,
    unlocked_at DATETIME NULL,

    PRIMARY KEY (user_id, achievement_id),

    CONSTRAINT fk_user_achievement_user
        FOREIGN KEY (user_id)
        REFERENCES user(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_user_achievement_achievement
        FOREIGN KEY (achievement_id)
        REFERENCES achievement(achievement_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 21. LIBRARY
-- =========================================================
CREATE TABLE library (
    user_id BIGINT UNSIGNED NOT NULL,
    app_id BIGINT UNSIGNED NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, app_id),

    CONSTRAINT fk_library_user
        FOREIGN KEY (user_id)
        REFERENCES user(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_library_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 22. WISHLIST
-- =========================================================
CREATE TABLE wishlist (
    user_id BIGINT UNSIGNED NOT NULL,
    app_id BIGINT UNSIGNED NOT NULL,
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, app_id),

    CONSTRAINT fk_wishlist_user
        FOREIGN KEY (user_id)
        REFERENCES user(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_wishlist_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- 23. PURCHASE
-- =========================================================
CREATE TABLE purchase (
    purchase_id BIGINT UNSIGNED AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    app_id BIGINT UNSIGNED NOT NULL,

    purchase_date DATETIME NOT NULL,
    price_paid DECIMAL(10,2) NOT NULL,

    payment_method VARCHAR(50) NULL,
    transaction_status ENUM(
        'COMPLETED',
        'REFUNDED',
        'CANCELLED'
    ) NOT NULL DEFAULT 'COMPLETED',

    PRIMARY KEY (purchase_id),

    CONSTRAINT fk_purchase_user
        FOREIGN KEY (user_id)
        REFERENCES user(user_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_purchase_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT chk_purchase_price
        CHECK (price_paid >= 0)
) ENGINE=InnoDB;


-- =========================================================
-- 24. USER_ACTIVITY
-- =========================================================
CREATE TABLE user_activity (
    activity_id BIGINT UNSIGNED AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    app_id BIGINT UNSIGNED NOT NULL,

    activity_type ENUM(
        'PLAY',
        'LAUNCH',
        'SESSION'
    ) NOT NULL,

    activity_time DATETIME NOT NULL,
    duration_minutes INT UNSIGNED NULL,

    PRIMARY KEY (activity_id),

    CONSTRAINT fk_activity_user
        FOREIGN KEY (user_id)
        REFERENCES user(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_activity_game
        FOREIGN KEY (app_id)
        REFERENCES game(app_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;


SHOW TABLES;

SELECT COUNT(*) AS table_count
FROM information_schema.tables
WHERE table_schema = 'steamscope'
  AND table_type = 'BASE TABLE';
USE steamscope;

ALTER TABLE game
MODIFY COLUMN support_email TEXT NULL;


SHOW COLUMNS FROM game LIKE 'name';


ALTER TABLE game
MODIFY COLUMN name VARCHAR(500) NOT NULL;
SHOW COLUMNS FROM game LIKE 'name';
