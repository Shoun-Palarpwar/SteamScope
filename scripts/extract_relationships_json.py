"""
STEAMSCOPE - REFERENCE & RELATIONSHIP EXTRACTION (JSON SOURCE)

Produces normalized reference names and game-to-attribute relationships
from the JSON source used by the current import pipeline.

Reads data/raw/games.json directly (developers/publishers/genres/
categories/supported_languages/full_audio_languages/screenshots
are already clean lists in the JSON; no fragile comma-splitting
needed). Note: `tags` is a dict of {tag_name: vote_count} in this
dataset, not a list -- handled accordingly.

Requires: pip install ijson

Output:
  data/cleaned/master/developer.csv   (name)
  data/cleaned/master/publisher.csv   (name)
  data/cleaned/master/genre.csv       (name)
  data/cleaned/master/tag.csv         (name)
  data/cleaned/master/category.csv    (name)
  data/cleaned/master/platform.csv    (name)
  data/cleaned/master/language.csv    (name)

  data/cleaned/relationships/game_developer.csv    (app_id, developer_name)
  data/cleaned/relationships/game_publisher.csv    (app_id, publisher_name)
  data/cleaned/relationships/game_genre.csv        (app_id, genre_name)
  data/cleaned/relationships/game_tag.csv          (app_id, tag_name)
  data/cleaned/relationships/game_category.csv     (app_id, category_name)
  data/cleaned/relationships/game_platform.csv     (app_id, platform_name)
  data/cleaned/relationships/game_language.csv     (app_id, language_name, support_type)
  data/cleaned/relationships/game_screenshot.csv   (app_id, screenshot_url)

These are name-keyed, not id-keyed -- the DB loader step (next)
will insert the master/*.csv names first, then use the resulting
MySQL-assigned ids to translate these relationship files into the
final game_* junction table inserts.
"""

import csv
import os
from pathlib import Path

import ijson

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data/raw/games.json"
MASTER_DIR = ROOT / "data/cleaned/master"
REL_DIR = ROOT / "data/cleaned/relationships"


def clean_str(value):
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def main():
    print("=" * 80)
    print("STEAMSCOPE - REFERENCE & RELATIONSHIP EXTRACTION (JSON SOURCE)")
    print("=" * 80)

    os.makedirs(MASTER_DIR, exist_ok=True)
    os.makedirs(REL_DIR, exist_ok=True)

    developers, publishers, genres = set(), set(), set()
    tags, categories, platforms, languages = set(), set(), set(), set()

    rel_files = {
        "game_developer": open(f"{REL_DIR}/game_developer.csv", "w", newline="", encoding="utf-8"),
        "game_publisher": open(f"{REL_DIR}/game_publisher.csv", "w", newline="", encoding="utf-8"),
        "game_genre": open(f"{REL_DIR}/game_genre.csv", "w", newline="", encoding="utf-8"),
        "game_tag": open(f"{REL_DIR}/game_tag.csv", "w", newline="", encoding="utf-8"),
        "game_category": open(f"{REL_DIR}/game_category.csv", "w", newline="", encoding="utf-8"),
        "game_platform": open(f"{REL_DIR}/game_platform.csv", "w", newline="", encoding="utf-8"),
        "game_language": open(f"{REL_DIR}/game_language.csv", "w", newline="", encoding="utf-8"),
        "game_screenshot": open(f"{REL_DIR}/game_screenshot.csv", "w", newline="", encoding="utf-8"),
    }

    writers = {name: csv.writer(fh) for name, fh in rel_files.items()}
    writers["game_developer"].writerow(["app_id", "developer_name"])
    writers["game_publisher"].writerow(["app_id", "publisher_name"])
    writers["game_genre"].writerow(["app_id", "genre_name"])
    writers["game_tag"].writerow(["app_id", "tag_name"])
    writers["game_category"].writerow(["app_id", "category_name"])
    writers["game_platform"].writerow(["app_id", "platform_name"])
    writers["game_language"].writerow(["app_id", "language_name", "support_type"])
    writers["game_screenshot"].writerow(["app_id", "screenshot_url"])

    total = 0

    print(f"\nReading: {RAW_FILE}\n")

    with open(RAW_FILE, "rb") as raw:
        for appid_str, obj in ijson.kvitems(raw, ""):
            total += 1

            try:
                app_id = int(appid_str)
            except (TypeError, ValueError):
                continue

            for d in obj.get("developers") or []:
                d = clean_str(d)
                if d:
                    developers.add(d)
                    writers["game_developer"].writerow([app_id, d])

            for p in obj.get("publishers") or []:
                p = clean_str(p)
                if p:
                    publishers.add(p)
                    writers["game_publisher"].writerow([app_id, p])

            for g in obj.get("genres") or []:
                g = clean_str(g)
                if g:
                    genres.add(g)
                    writers["game_genre"].writerow([app_id, g])

            for c in obj.get("categories") or []:
                c = clean_str(c)
                if c:
                    categories.add(c)
                    writers["game_category"].writerow([app_id, c])

            # tags is a dict {name: vote_count}, not a list
            tag_field = obj.get("tags") or {}
            if isinstance(tag_field, dict):
                tag_iter = tag_field.keys()
            else:
                tag_iter = tag_field  # fallback if ever a list
            for t in tag_iter:
                t = clean_str(t)
                if t:
                    tags.add(t)
                    writers["game_tag"].writerow([app_id, t])

            if obj.get("windows"):
                platforms.add("Windows")
                writers["game_platform"].writerow([app_id, "Windows"])
            if obj.get("mac"):
                platforms.add("Mac")
                writers["game_platform"].writerow([app_id, "Mac"])
            if obj.get("linux"):
                platforms.add("Linux")
                writers["game_platform"].writerow([app_id, "Linux"])

            for lang in obj.get("supported_languages") or []:
                lang = clean_str(lang)
                if lang:
                    languages.add(lang)
                    writers["game_language"].writerow([app_id, lang, "SUPPORTED"])

            for lang in obj.get("full_audio_languages") or []:
                lang = clean_str(lang)
                if lang:
                    languages.add(lang)
                    writers["game_language"].writerow([app_id, lang, "FULL_AUDIO"])

            for shot in obj.get("screenshots") or []:
                shot = clean_str(shot)
                if shot:
                    writers["game_screenshot"].writerow([app_id, shot])

            if total % 10000 == 0:
                print(f"Processed: {total:,}", end="\r")

    for fh in rel_files.values():
        fh.close()

    # -------------------------------------------------------
    # Write master (lookup) tables
    # -------------------------------------------------------

    def write_master(filename, values):
        path = f"{MASTER_DIR}/{filename}"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name"])
            for v in sorted(values, key=lambda x: x.lower()):
                w.writerow([v])
        return path

    write_master("developer.csv", developers)
    write_master("publisher.csv", publishers)
    write_master("genre.csv", genres)
    write_master("tag.csv", tags)
    write_master("category.csv", categories)
    write_master("platform.csv", platforms)
    write_master("language.csv", languages)

    print(f"\n\n{'=' * 80}")
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Records scanned: {total:,}")
    print(f"Developer : {len(developers):,}")
    print(f"Publisher : {len(publishers):,}")
    print(f"Genre     : {len(genres):,}")
    print(f"Tag       : {len(tags):,}")
    print(f"Category  : {len(categories):,}")
    print(f"Platform  : {len(platforms):,}")
    print(f"Language  : {len(languages):,}")
    print(f"\nMaster tables:       {MASTER_DIR}")
    print(f"Relationship tables: {REL_DIR}")


if __name__ == "__main__":
    main()
