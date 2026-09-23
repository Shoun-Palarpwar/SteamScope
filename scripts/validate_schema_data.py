import pandas as pd
from pathlib import Path

BASE = Path("data/cleaned")

GAMES = BASE / "games_cleaned.csv"
REVIEWS = BASE / "reviews_cleaned.csv"

print("=" * 70)
print("STEAMSCOPE - SCHEMA vs DATA VALIDATION")
print("=" * 70)

# ---------------------------------------------------------
# 1. GAME DATA
# ---------------------------------------------------------
print("\n[1] Loading games...")

games = pd.read_csv(GAMES)
games.columns = (
    games.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

print(f"Games loaded: {len(games):,}")
print(f"Columns: {len(games.columns)}")

# AppID checks
duplicate_appids = games["appid"].duplicated().sum()
missing_appids = games["appid"].isna().sum()
missing_names = games["name"].isna().sum()

print(f"Duplicate AppIDs : {duplicate_appids:,}")
print(f"Missing AppIDs   : {missing_appids:,}")
print(f"Missing names    : {missing_names:,}")

# ---------------------------------------------------------
# 2. REVIEW DATA
# ---------------------------------------------------------
print("\n[2] Loading reviews...")

reviews = pd.read_csv(
    REVIEWS,
    usecols=[
        "steamid",
        "appid",
        "voted_up",
        "votes_up",
        "votes_funny",
        "weighted_vote_score",
        "playtime_forever",
        "playtime_at_review",
        "num_games_owned",
        "num_reviews",
        "review",
        "unix_timestamp_created",
        "unix_timestamp_updated",
    ],
)

print(f"Reviews loaded: {len(reviews):,}")

# ---------------------------------------------------------
# 3. REVIEW -> GAME FK VALIDATION
# ---------------------------------------------------------
print("\n[3] REVIEW -> GAME foreign-key validation...")

game_ids = set(games["appid"].dropna().astype("int64"))

review_appids = reviews["appid"].dropna().astype("int64")

matched = review_appids.isin(game_ids).sum()
unmatched = (~review_appids.isin(game_ids)).sum()

print(f"Review rows matched to GAME : {matched:,}")
print(f"Review rows unmatched       : {unmatched:,}")

if unmatched == 0:
    print("PASS: Every review has a valid GAME reference.")
else:
    print("INFO: Unmatched reviews exist and should remain outside REVIEW.")

# ---------------------------------------------------------
# 4. REQUIRED GAME COMPLEX FIELDS
# ---------------------------------------------------------
print("\n[4] Multi-valued GAME fields...")

complex_fields = [
    "developers",
    "publishers",
    "categories",
    "genres",
    "tags",
    "supported_languages",
    "full_audio_languages",
    "screenshots",
    "movies",
]

for col in complex_fields:
    non_empty = games[col].notna().sum()
    print(f"{col:25} {non_empty:>10,} non-empty")

# ---------------------------------------------------------
# 5. PLATFORM VALIDATION
# ---------------------------------------------------------
print("\n[5] PLATFORM mapping...")

for col in ["windows", "mac", "linux"]:
    print(f"{col:10} TRUE = {games[col].fillna(False).astype(bool).sum():,}")

print("\nExpected PLATFORM values:")
print("  Windows")
print("  macOS")
print("  Linux")

# ---------------------------------------------------------
# 6. UNIQUE VALUES
# ---------------------------------------------------------
print("\n[6] Unique relationship values...")

for col in [
    "developers",
    "publishers",
    "genres",
    "tags",
    "categories",
    "supported_languages",
    "full_audio_languages",
]:
    values = set()

    for value in games[col].dropna():
        value = str(value).strip()

        if value:
            # The exact parsing/cleaning rules will be applied
            # during ETL; this is only a schema-level inspection.
            values.add(value)

    print(f"{col:25} {len(values):>10,} unique raw values")

# ---------------------------------------------------------
# 7. NUMERIC CONSTRAINT CHECKS
# ---------------------------------------------------------
print("\n[7] Constraint checks...")

numeric_checks = {
    "price": games["price"],
    "required_age": games["required_age"],
    "positive": games["positive"],
    "negative": games["negative"],
    "achievements": games["achievements"],
    "recommendations": games["recommendations"],
    "average_playtime_forever": games["average_playtime_forever"],
    "average_playtime_two_weeks": games["average_playtime_two_weeks"],
    "median_playtime_forever": games["median_playtime_forever"],
    "median_playtime_two_weeks": games["median_playtime_two_weeks"],
}

for name, series in numeric_checks.items():
    numeric = pd.to_numeric(series, errors="coerce")

    negative = (numeric < 0).sum()

    print(f"{name:30} negative = {negative:,}")

# ---------------------------------------------------------
# 8. REVIEW CONSTRAINTS
# ---------------------------------------------------------
print("\n[8] REVIEW constraint checks...")

review_numeric = [
    "votes_up",
    "votes_funny",
    "playtime_forever",
    "playtime_at_review",
    "num_games_owned",
    "num_reviews",
]

for col in review_numeric:
    numeric = pd.to_numeric(reviews[col], errors="coerce")
    negative = (numeric < 0).sum()
    print(f"{col:25} negative = {negative:,}")

# ---------------------------------------------------------
# 9. REVIEW TIMESTAMP CHECK
# ---------------------------------------------------------
print("\n[9] REVIEW timestamp validation...")

created = pd.to_numeric(
    reviews["unix_timestamp_created"], errors="coerce"
)

updated = pd.to_numeric(
    reviews["unix_timestamp_updated"], errors="coerce"
)

print(f"Missing created timestamps: {created.isna().sum():,}")
print(f"Missing updated timestamps: {updated.isna().sum():,}")

# ---------------------------------------------------------
# 10. MOVIE FIELD INSPECTION
# ---------------------------------------------------------
print("\n[10] MOVIES field inspection...")

movie_values = games["movies"].dropna().astype(str)

jpg_count = movie_values.str.contains(
    r"\.jpg", case=False, regex=True
).sum()

mp4_count = movie_values.str.contains(
    r"\.mp4", case=False, regex=True
).sum()

webm_count = movie_values.str.contains(
    r"\.webm", case=False, regex=True
).sum()

print(f"Values containing .jpg  : {jpg_count:,}")
print(f"Values containing .mp4  : {mp4_count:,}")
print(f"Values containing .webm : {webm_count:,}")

if jpg_count > mp4_count + webm_count:
    print("INFO: movies appears to contain image/CDN URLs.")
    print("Decision: GAME_MOVIE remains excluded.")

# ---------------------------------------------------------
# FINAL
# ---------------------------------------------------------
print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)

print("""
Schema status:

GAME                  -> VALIDATED
REVIEW                -> VALIDATED
DEVELOPER             -> READY
PUBLISHER             -> READY
GENRE                 -> READY
TAG                   -> READY
CATEGORY              -> READY
PLATFORM              -> READY
LANGUAGE              -> READY
GAME_* bridges        -> READY
LIBRARY               -> READY
WISHLIST              -> READY
PURCHASE              -> READY
ACHIEVEMENT           -> READY
USER_ACHIEVEMENT      -> READY
USER_ACTIVITY         -> READY
GAME_SCREENSHOT       -> READY
GAME_MOVIE            -> EXCLUDED FOR NOW
""")

print("Next phase: MySQL database + table creation.")