-- Apply once to the selected SteamScope database; existing rows start unfavorited.
ALTER TABLE `library` ADD COLUMN is_favorite BOOLEAN NOT NULL DEFAULT FALSE;
