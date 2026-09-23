"""
STEAMSCOPE - REFERENCE & JUNCTION TABLE LOADER

Loads data/cleaned/master/*.csv into the reference tables
(developer, publisher, genre, tag, category, platform, language),
then uses the MySQL-assigned ids to translate
data/cleaned/relationships/*.csv into the game_* junction tables.

Requires: game table already populated (FKs point at game.app_id).

Idempotent: each table is skipped if it already has rows, so this
is safe to re-run after a partial failure without creating
duplicates or crashing on already-loaded tables.
"""

import csv
from pathlib import Path

import mysql.connector

BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_DIR = BASE_DIR / "data" / "cleaned" / "master"
REL_DIR = BASE_DIR / "data" / "cleaned" / "relationships"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "steamscope",
}

BATCH_SIZE = 2000

SIMPLE_TABLES = [
    ("developer.csv", "developer", "developer_id"),
    ("publisher.csv", "publisher", "publisher_id"),
    ("genre.csv", "genre", "genre_id"),
    ("tag.csv", "tag", "tag_id"),
    ("category.csv", "category", "category_id"),
    ("platform.csv", "platform", "platform_id"),
    ("language.csv", "language", "language_id"),
]

JUNCTION_TABLES = [
    ("game_developer.csv", "game_developer", "developer_id", "developer_name", "developer"),
    ("game_publisher.csv", "game_publisher", "publisher_id", "publisher_name", "publisher"),
    ("game_genre.csv", "game_genre", "genre_id", "genre_name", "genre"),
    ("game_tag.csv", "game_tag", "tag_id", "tag_name", "tag"),
    ("game_category.csv", "game_category", "category_id", "category_name", "category"),
    ("game_platform.csv", "game_platform", "platform_id", "platform_name", "platform"),
]


def table_count(cursor, table):
    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
    return cursor.fetchone()[0]


def load_lookup_table(cursor, connection, filename, table, id_col):
    """Insert unique names (if not already loaded), then return name -> id map."""
    existing = table_count(cursor, table)

    if existing == 0:
        path = MASTER_DIR / filename
        names = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("name") or "").strip()
                if name:
                    names.append((name,))

        insert_sql = f"INSERT IGNORE INTO `{table}` (name) VALUES (%s)"
        for i in range(0, len(names), BATCH_SIZE):
            cursor.executemany(insert_sql, names[i:i + BATCH_SIZE])
        connection.commit()
        print(f"  {table}: inserted {len(names):,} names")
    else:
        print(f"  {table}: already has {existing:,} rows, skipping insert")

    cursor.execute(f"SELECT {id_col}, name FROM `{table}`")
    return {name: id_ for id_, name in cursor.fetchall()}


def load_junction(cursor, connection, filename, table, id_col, name_field, name_to_id, label):
    """Translate (app_id, name) relationship rows into (app_id, id) junction rows."""
    existing = table_count(cursor, table)

    if existing > 0:
        print(f"  {table}: already has {existing:,} rows, skipping")
        return

    path = REL_DIR / filename
    rows = []
    unmatched = 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            app_id = row.get("app_id")
            name = (row.get(name_field) or "").strip()
            id_ = name_to_id.get(name)
            if app_id and id_ is not None:
                rows.append((app_id, id_))
            else:
                unmatched += 1

    insert_sql = f"INSERT IGNORE INTO `{table}` (app_id, {id_col}) VALUES (%s, %s)"
    for i in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(insert_sql, rows[i:i + BATCH_SIZE])
    connection.commit()
    print(f"  {table}: inserted {len(rows):,} rows (unmatched: {unmatched:,})")


def load_languages(cursor, connection, language_to_id):
    existing = table_count(cursor, "game_language")
    if existing > 0:
        print(f"  game_language: already has {existing:,} rows, skipping")
        return

    path = REL_DIR / "game_language.csv"
    rows = []
    unmatched = 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            app_id = row.get("app_id")
            name = (row.get("language_name") or "").strip()
            support_type = (row.get("support_type") or "").strip()
            id_ = language_to_id.get(name)
            if app_id and id_ is not None and support_type:
                rows.append((app_id, id_, support_type))
            else:
                unmatched += 1

    insert_sql = (
        "INSERT IGNORE INTO game_language (app_id, language_id, support_type) "
        "VALUES (%s, %s, %s)"
    )
    for i in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(insert_sql, rows[i:i + BATCH_SIZE])
    connection.commit()
    print(f"  game_language: inserted {len(rows):,} rows (unmatched: {unmatched:,})")


def load_screenshots(cursor, connection):
    existing = table_count(cursor, "game_screenshot")
    if existing > 0:
        print(f"  game_screenshot: already has {existing:,} rows, skipping")
        return

    path = REL_DIR / "game_screenshot.csv"
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            app_id = row.get("app_id")
            url = (row.get("screenshot_url") or "").strip()
            if app_id and url:
                rows.append((app_id, url))

    insert_sql = "INSERT INTO game_screenshot (app_id, screenshot_url) VALUES (%s, %s)"
    for i in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(insert_sql, rows[i:i + BATCH_SIZE])
    connection.commit()
    print(f"  game_screenshot: inserted {len(rows):,} rows")


def main():
    print("=" * 70)
    print("STEAMSCOPE - REFERENCE & JUNCTION TABLE LOADER")
    print("=" * 70)

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    print("\nMySQL connection: PASS")

    try:
        game_count = table_count(cursor, "game")
        print(f"game table rows: {game_count:,}")
        if game_count == 0:
            raise RuntimeError("game table is empty. Run load_games.py first.")

        print("\n[1] Loading reference tables...")
        name_maps = {}
        for filename, table, id_col in SIMPLE_TABLES:
            name_maps[table] = load_lookup_table(
                cursor, connection, filename, table, id_col
            )

        print("\n[2] Loading junction tables...")
        for filename, table, id_col, name_field, lookup_key in JUNCTION_TABLES:
            load_junction(
                cursor, connection, filename, table, id_col,
                name_field, name_maps[lookup_key], table
            )

        print("\n[3] Loading game_language...")
        load_languages(cursor, connection, name_maps["language"])

        print("\n[4] Loading game_screenshot...")
        load_screenshots(cursor, connection)

        print("\n" + "=" * 70)
        print("PASS: Reference & junction load completed.")
        print("=" * 70)
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()