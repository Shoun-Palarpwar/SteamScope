import pandas as pd
from pathlib import Path
import re

# --------------------------------------------------
# Paths
# --------------------------------------------------

INPUT_FILE = Path("data/cleaned/games_cleaned.csv")
OUTPUT_DIR = Path("data/cleaned/master")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Load dataset
# --------------------------------------------------

print("Loading games_cleaned.csv...")

df = pd.read_csv(
    INPUT_FILE,
    dtype={"AppID": "string"},
    low_memory=False
)

print(f"Games loaded: {len(df):,}")

# --------------------------------------------------
# Normalize column names
# --------------------------------------------------

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# --------------------------------------------------
# Helper functions
# --------------------------------------------------

MISSING_VALUES = {
    "",
    "nan",
    "none",
    "null",
    "n/a",
    "na"
}


def clean_value(value):
    """Clean a single catalog value without inventing data."""

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value.lower() in MISSING_VALUES:
        return None

    return value


def split_values(value):
    """
    Split multi-valued catalog fields.

    Handles comma-separated values while preserving
    meaningful text as much as possible.
    """

    value = clean_value(value)

    if value is None:
        return []

    # Most Steam catalog fields use commas to separate values.
    parts = re.split(r"\s*,\s*", value)

    result = []

    for part in parts:
        part = part.strip()

        if not part:
            continue

        if part.lower() in MISSING_VALUES:
            continue

        result.append(part)

    return result


def extract_unique_simple(column):
    """Extract unique values from a simple multi-value column."""

    values = set()

    for value in df[column]:
        for item in split_values(value):
            values.add(item)

    return sorted(values, key=lambda x: x.lower())


# --------------------------------------------------
# 1. Developers
# --------------------------------------------------

print("\nExtracting developers...")

developers = extract_unique_simple("developers")

developer_df = pd.DataFrame({
    "name": developers
})

developer_df.to_csv(
    OUTPUT_DIR / "developer.csv",
    index=False
)

print(f"Developers: {len(developer_df):,}")


# --------------------------------------------------
# 2. Publishers
# --------------------------------------------------

print("\nExtracting publishers...")

publishers = extract_unique_simple("publishers")

publisher_df = pd.DataFrame({
    "name": publishers
})

publisher_df.to_csv(
    OUTPUT_DIR / "publisher.csv",
    index=False
)

print(f"Publishers: {len(publisher_df):,}")


# --------------------------------------------------
# 3. Genres
# --------------------------------------------------

print("\nExtracting genres...")

genres = extract_unique_simple("genres")

genre_df = pd.DataFrame({
    "name": genres
})

genre_df.to_csv(
    OUTPUT_DIR / "genre.csv",
    index=False
)

print(f"Genres: {len(genre_df):,}")


# --------------------------------------------------
# 4. Tags
# --------------------------------------------------

print("\nExtracting tags...")

tags = extract_unique_simple("tags")

tag_df = pd.DataFrame({
    "name": tags
})

tag_df.to_csv(
    OUTPUT_DIR / "tag.csv",
    index=False
)

print(f"Tags: {len(tag_df):,}")


# --------------------------------------------------
# 5. Categories
# --------------------------------------------------

print("\nExtracting categories...")
    
categories = extract_unique_simple("categories")

category_df = pd.DataFrame({
    "name": categories
})

category_df.to_csv(
    OUTPUT_DIR / "category.csv",
    index=False
)

print(f"Categories: {len(category_df):,}")


# --------------------------------------------------
# 6. Platforms
# --------------------------------------------------

print("\nExtracting platforms...")

platforms = set()

for _, row in df.iterrows():

    if str(row.get("windows", "")).strip().lower() == "true":
        platforms.add("Windows")

    if str(row.get("mac", "")).strip().lower() == "true":
        platforms.add("Mac")

    if str(row.get("linux", "")).strip().lower() == "true":
        platforms.add("Linux")


platform_df = pd.DataFrame({
    "name": sorted(platforms)
})

platform_df.to_csv(
    OUTPUT_DIR / "platform.csv",
    index=False
)

print(f"Platforms: {len(platform_df):,}")


# --------------------------------------------------
# 7. Languages
# --------------------------------------------------

print("\nExtracting languages...")

import ast
import re
import html


def clean_language_name(value):
    """Clean one language label without inventing information."""

    if value is None or pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    # Decode HTML entities repeatedly.
    # Example:
    # &amp;amp;lt; -> &lt; -> <
    for _ in range(5):
        decoded = html.unescape(text)
        if decoded == text:
            break
        text = decoded

    # Convert escaped/newline separators into spaces.
    text = text.replace("\\r\\n", "\n")
    text = text.replace("\\n", "\n")
    text = text.replace("\\r", "\n")

    # Remove HTML tags.
    text = re.sub(r"<[^>]+>", "", text)

    # Remove BBCode tags such as [b][/b].
    text = re.sub(r"\[[^\]]*\]", "", text)

    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return None

    return text


def extract_language_list(value):
    """
    Parse language fields stored as Python-style lists.

    Examples:
        ['English']
        ['English', 'French', 'German']

    Also handles malformed but recoverable source values.
    """

    if value is None or pd.isna(value):
        return []

    text = str(value).strip()

    if not text:
        return []

    # Normal case: Python-style list.
    try:
        parsed = ast.literal_eval(text)

        if isinstance(parsed, list):
            raw_items = parsed
        else:
            raw_items = [parsed]

    except (ValueError, SyntaxError):
        raw_items = [text]

    result = []

    for item in raw_items:

        if item is None:
            continue

        item = str(item).strip()

        # Some malformed records contain several languages
        # separated by escaped/newline characters.
        item = item.replace("\\r\\n", "\n")
        item = item.replace("\\n", "\n")
        item = item.replace("\\r", "\n")

        parts = re.split(r"[\n,]+", item)

        for part in parts:

            cleaned = clean_language_name(part)

            if cleaned:
                result.append(cleaned)

    return result


languages = set()

for column in ["supported_languages", "full_audio_languages"]:

    for value in df[column]:

        for language in extract_language_list(value):
            languages.add(language)


language_df = pd.DataFrame({
    "name": sorted(languages, key=lambda x: x.lower())
})

language_df.to_csv(
    OUTPUT_DIR / "language.csv",
    index=False
)

print(f"Languages: {len(language_df):,}")


# --------------------------------------------------
# Final summary
# --------------------------------------------------

print("\n" + "=" * 50)
print("MASTER TABLE EXTRACTION COMPLETE")
print("=" * 50)

print(f"Developer : {len(developer_df):,}")
print(f"Publisher : {len(publisher_df):,}")
print(f"Genre     : {len(genre_df):,}")
print(f"Tag       : {len(tag_df):,}")
print(f"Category  : {len(category_df):,}")
print(f"Platform  : {len(platform_df):,}")
print(f"Language  : {len(language_df):,}")

print("\nOutput directory:")
print(OUTPUT_DIR.resolve())