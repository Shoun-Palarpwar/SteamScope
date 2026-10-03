-- SteamScope: fresh schema from saved SHOW CREATE TABLE evidence.
-- Snapshot: 2026-10-02T11:57:12.132880+05:30
-- Includes library.is_favorite. Do not apply migration 001 afterward.
-- EMPTY database only; no tables are dropped or overwritten.
CREATE DATABASE IF NOT EXISTS steamscope CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE steamscope;

CREATE TABLE `category` (
  `category_id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `developer` (
  `developer_id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`developer_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `game` (
  `app_id` bigint unsigned NOT NULL,
  `name` varchar(512) NOT NULL,
  `release_date` date DEFAULT NULL,
  `estimated_owners` varchar(100) DEFAULT NULL,
  `peak_ccu` int unsigned DEFAULT NULL,
  `required_age` int unsigned DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `discount_dlc_count` int unsigned DEFAULT NULL,
  `description` longtext,
  `header_image_url` text,
  `website_url` text,
  `support_url` text,
  `support_email` varchar(255) DEFAULT NULL,
  `metacritic_score` int unsigned DEFAULT NULL,
  `metacritic_url` text,
  `user_score` decimal(5,2) DEFAULT NULL,
  `positive_reviews` int unsigned DEFAULT NULL,
  `negative_reviews` int unsigned DEFAULT NULL,
  `score_rank` int unsigned DEFAULT NULL,
  `achievement_count` int unsigned DEFAULT NULL,
  `recommendation_count` int unsigned DEFAULT NULL,
  `notes` longtext,
  `avg_playtime_forever` int unsigned DEFAULT NULL,
  `avg_playtime_2weeks` int unsigned DEFAULT NULL,
  `median_playtime_forever` int unsigned DEFAULT NULL,
  `median_playtime_2weeks` int unsigned DEFAULT NULL,
  PRIMARY KEY (`app_id`),
  CONSTRAINT `chk_game_metacritic` CHECK (((`metacritic_score` is null) or (`metacritic_score` between 0 and 100))),
  CONSTRAINT `chk_game_price` CHECK (((`price` is null) or (`price` >= 0))),
  CONSTRAINT `chk_game_required_age` CHECK (((`required_age` is null) or (`required_age` >= 0))),
  CONSTRAINT `chk_game_user_score` CHECK (((`user_score` is null) or (`user_score` >= 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `genre` (
  `genre_id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`genre_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `language` (
  `language_id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`language_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `platform` (
  `platform_id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`platform_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `publisher` (
  `publisher_id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`publisher_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `tag` (
  `tag_id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`tag_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user` (
  `user_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uq_user_username` (`username`),
  UNIQUE KEY `uq_user_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `achievement` (
  `achievement_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `app_id` bigint unsigned NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text,
  `unlock_percentage` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`achievement_id`),
  KEY `fk_achievement_game` (`app_id`),
  CONSTRAINT `fk_achievement_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `game_category` (
  `app_id` bigint unsigned NOT NULL,
  `category_id` int unsigned NOT NULL,
  PRIMARY KEY (`app_id`,`category_id`),
  KEY `fk_game_category_category` (`category_id`),
  CONSTRAINT `fk_game_category_category` FOREIGN KEY (`category_id`) REFERENCES `category` (`category_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_game_category_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `game_developer` (
  `app_id` bigint unsigned NOT NULL,
  `developer_id` int unsigned NOT NULL,
  PRIMARY KEY (`app_id`,`developer_id`),
  KEY `fk_game_developer_developer` (`developer_id`),
  CONSTRAINT `fk_game_developer_developer` FOREIGN KEY (`developer_id`) REFERENCES `developer` (`developer_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_game_developer_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `game_genre` (
  `app_id` bigint unsigned NOT NULL,
  `genre_id` int unsigned NOT NULL,
  PRIMARY KEY (`app_id`,`genre_id`),
  KEY `fk_game_genre_genre` (`genre_id`),
  CONSTRAINT `fk_game_genre_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_game_genre_genre` FOREIGN KEY (`genre_id`) REFERENCES `genre` (`genre_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `game_language` (
  `app_id` bigint unsigned NOT NULL,
  `language_id` int unsigned NOT NULL,
  `support_type` enum('SUPPORTED','FULL_AUDIO') NOT NULL,
  PRIMARY KEY (`app_id`,`language_id`,`support_type`),
  KEY `fk_game_language_language` (`language_id`),
  CONSTRAINT `fk_game_language_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_game_language_language` FOREIGN KEY (`language_id`) REFERENCES `language` (`language_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `game_platform` (
  `app_id` bigint unsigned NOT NULL,
  `platform_id` int unsigned NOT NULL,
  PRIMARY KEY (`app_id`,`platform_id`),
  KEY `fk_game_platform_platform` (`platform_id`),
  CONSTRAINT `fk_game_platform_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_game_platform_platform` FOREIGN KEY (`platform_id`) REFERENCES `platform` (`platform_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `game_publisher` (
  `app_id` bigint unsigned NOT NULL,
  `publisher_id` int unsigned NOT NULL,
  PRIMARY KEY (`app_id`,`publisher_id`),
  KEY `fk_game_publisher_publisher` (`publisher_id`),
  CONSTRAINT `fk_game_publisher_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_game_publisher_publisher` FOREIGN KEY (`publisher_id`) REFERENCES `publisher` (`publisher_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `game_screenshot` (
  `screenshot_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `app_id` bigint unsigned NOT NULL,
  `screenshot_url` text NOT NULL,
  PRIMARY KEY (`screenshot_id`),
  KEY `fk_game_screenshot_game` (`app_id`),
  CONSTRAINT `fk_game_screenshot_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `game_tag` (
  `app_id` bigint unsigned NOT NULL,
  `tag_id` int unsigned NOT NULL,
  PRIMARY KEY (`app_id`,`tag_id`),
  KEY `fk_game_tag_tag` (`tag_id`),
  CONSTRAINT `fk_game_tag_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_game_tag_tag` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`tag_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `library` (
  `user_id` bigint unsigned NOT NULL,
  `app_id` bigint unsigned NOT NULL,
  `added_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_favorite` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`user_id`,`app_id`),
  KEY `fk_library_game` (`app_id`),
  CONSTRAINT `fk_library_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_library_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `purchase` (
  `purchase_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `app_id` bigint unsigned NOT NULL,
  `purchase_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `price_paid` decimal(10,2) NOT NULL,
  `payment_method` varchar(50) DEFAULT NULL,
  `transaction_status` enum('COMPLETED','REFUNDED','CANCELLED') NOT NULL DEFAULT 'COMPLETED',
  PRIMARY KEY (`purchase_id`),
  KEY `fk_purchase_user` (`user_id`),
  KEY `fk_purchase_game` (`app_id`),
  CONSTRAINT `fk_purchase_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_purchase_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `review` (
  `review_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `steamid` bigint unsigned DEFAULT NULL,
  `app_id` bigint unsigned NOT NULL,
  `voted_up` tinyint(1) DEFAULT NULL,
  `votes_up` int unsigned DEFAULT NULL,
  `votes_funny` int unsigned DEFAULT NULL,
  `weighted_vote_score` decimal(10,8) DEFAULT NULL,
  `playtime_forever` int unsigned DEFAULT NULL,
  `playtime_at_review` int unsigned DEFAULT NULL,
  `num_games_owned` int unsigned DEFAULT NULL,
  `num_reviews` int unsigned DEFAULT NULL,
  `review_text` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`review_id`),
  KEY `fk_review_game` (`app_id`),
  CONSTRAINT `fk_review_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user_activity` (
  `activity_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `app_id` bigint unsigned NOT NULL,
  `activity_type` enum('PLAY','LAUNCH','SESSION') NOT NULL,
  `activity_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `duration_minutes` int unsigned DEFAULT NULL,
  PRIMARY KEY (`activity_id`),
  KEY `fk_user_activity_user` (`user_id`),
  KEY `fk_user_activity_game` (`app_id`),
  CONSTRAINT `fk_user_activity_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_user_activity_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `wishlist` (
  `user_id` bigint unsigned NOT NULL,
  `app_id` bigint unsigned NOT NULL,
  `added_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`app_id`),
  KEY `fk_wishlist_game` (`app_id`),
  CONSTRAINT `fk_wishlist_game` FOREIGN KEY (`app_id`) REFERENCES `game` (`app_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_wishlist_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `user_achievement` (
  `user_id` bigint unsigned NOT NULL,
  `achievement_id` bigint unsigned NOT NULL,
  `unlocked_at` datetime DEFAULT NULL,
  PRIMARY KEY (`user_id`,`achievement_id`),
  KEY `fk_user_achievement_achievement` (`achievement_id`),
  CONSTRAINT `fk_user_achievement_achievement` FOREIGN KEY (`achievement_id`) REFERENCES `achievement` (`achievement_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_user_achievement_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

