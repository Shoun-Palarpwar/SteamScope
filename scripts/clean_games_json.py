"""
STEAMSCOPE - GAMES DATA CLEANING (JSON SOURCE)

Reads data/raw/games.json instead of
data/raw/games.csv, because the CSV export has corrupted column
alignment in the investigated sample. The JSON source keeps fields
explicitly named; exact historical corruption percentages were not verified.

Streams the file with ijson rather than json.load(), since the
raw file is ~950MB and loading it fully into memory as a Python
dict first is unnecessary and risky on lower-RAM machines.

Requires: pip install ijson

Output columns match exactly what scripts/load_games.py expects,
so load_games.py itself does not need to change.
"""

import csv
import os
from pathlib import Path

import ijson

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data/raw/games.json"
OUTPUT_FILE = ROOT / "data/cleaned/games_cleaned.csv"

FIELDNAMES = [
    "appid",
    "name",
    "release_date",
    "estimated_owners",
    "peak_ccu",
    "required_age",
    "price",
    "discountdlc_count",
    "about_the_game",
    "header_image",
    "website",
    "support_url",
    "support_email",
    "metacritic_score",
    "metacritic_url",
    "user_score",
    "positive",
    "negative",
    "score_rank",
    "achievements",
    "recommendations",
    "notes",
    "average_playtime_forever",
    "average_playtime_two_weeks",
    "median_playtime_forever",
    "median_playtime_two_weeks",
]


def clean(value):
    """Trim strings; convert empty string to None. Leave numbers as-is."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    return value


def main():
    print("=" * 80)
    print("STEAMSCOPE - GAMES DATA CLEANING (JSON SOURCE)")
    print("=" * 80)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    total = 0
    written = 0
    missing_name = 0
    duplicate_appids = 0
    seen_appids = set()

    print(f"\nReading: {RAW_FILE}")
    print(f"Writing: {OUTPUT_FILE}\n")

    with open(RAW_FILE, "rb") as raw, \
         open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as out:

        writer = csv.DictWriter(out, fieldnames=FIELDNAMES)
        writer.writeheader()

        for appid_str, obj in ijson.kvitems(raw, ""):
            total += 1

            name = clean(obj.get("name"))
            if name is None:
                missing_name += 1
                continue

            try:
                app_id = int(appid_str)
            except (TypeError, ValueError):
                continue

            if app_id in seen_appids:
                duplicate_appids += 1
                continue
            seen_appids.add(app_id)

            writer.writerow({
                "appid": app_id,
                "name": name,
                "release_date": clean(obj.get("release_date")),
                "estimated_owners": clean(obj.get("estimated_owners")),
                "peak_ccu": obj.get("peak_ccu"),
                "required_age": obj.get("required_age"),
                "price": obj.get("price"),
                "discountdlc_count": obj.get("dlc_count"),
                "about_the_game": clean(obj.get("about_the_game")),
                "header_image": clean(obj.get("header_image")),
                "website": clean(obj.get("website")),
                "support_url": clean(obj.get("support_url")),
                "support_email": clean(obj.get("support_email")),
                "metacritic_score": obj.get("metacritic_score"),
                "metacritic_url": clean(obj.get("metacritic_url")),
                "user_score": obj.get("user_score"),
                "positive": obj.get("positive"),
                "negative": obj.get("negative"),
                "score_rank": clean(obj.get("score_rank")),
                "achievements": obj.get("achievements"),
                "recommendations": obj.get("recommendations"),
                "notes": clean(obj.get("notes")),
                "average_playtime_forever": obj.get("average_playtime_forever"),
                "average_playtime_two_weeks": obj.get("average_playtime_2weeks"),
                "median_playtime_forever": obj.get("median_playtime_forever"),
                "median_playtime_two_weeks": obj.get("median_playtime_2weeks"),
            })

            written += 1

            if total % 10000 == 0:
                print(f"Processed: {total:,}", end="\r")

    print(f"\n\n{'=' * 80}")
    print("CLEANING SUMMARY")
    print("=" * 80)
    print(f"Records scanned:            {total:,}")
    print(f"Rows written:               {written:,}")
    print(f"Skipped (missing name):     {missing_name:,}")
    print(f"Skipped (duplicate AppID):  {duplicate_appids:,}")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
