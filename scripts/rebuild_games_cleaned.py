import csv
import os

RAW_FILE = "data/raw/games.csv"
OUTPUT_FILE = "data/cleaned/games_cleaned.csv"
TEMP_FILE = "data/cleaned/games_cleaned_temp.csv"

EXPECTED_RAW_FIELDS = 40
EXPECTED_CLEAN_FIELDS = 39


CLEANED_HEADER = [
    "AppID",
    "Name",
    "Release date",
    "Estimated owners",
    "Peak CCU",
    "Required age",
    "Price",
    "DiscountDLC count",
    "About the game",
    "Supported languages",
    "Full audio languages",
    "Reviews",
    "Header image",
    "Website",
    "Support url",
    "Support email",
    "Windows",
    "Mac",
    "Linux",
    "Metacritic score",
    "Metacritic url",
    "User score",
    "Positive",
    "Negative",
    "Score rank",
    "Achievements",
    "Recommendations",
    "Notes",
    "Average playtime forever",
    "Average playtime two weeks",
    "Median playtime forever",
    "Median playtime two weeks",
    "Developers",
    "Publishers",
    "Categories",
    "Genres",
    "Tags",
    "Screenshots",
    "Movies",
]


def clean_missing(value):
    if value is None:
        return ""

    value = value.strip()

    if value.lower() in {"none", "nan", "null"}:
        return ""

    return value


def transform_row(row):

    if len(row) != EXPECTED_RAW_FIELDS:
        raise ValueError(
            f"Expected {EXPECTED_RAW_FIELDS} fields, "
            f"got {len(row)} for AppID {row[0]}"
        )

    # ---------------------------------------------------------------
    # IMPORTANT RAW DATASET CORRECTION
    #
    # Raw positions 12-39 are shifted by one position relative to
    # the 39-column header.
    #
    # Raw 12 = extra/empty field
    # Raw 13 = Header image
    # Raw 14 = Website
    # Raw 15 = Support URL
    # Raw 16 = Support Email
    # Raw 17 = Windows
    # ...
    # Raw 39 = Movies
    # ---------------------------------------------------------------

    cleaned = [
        clean_missing(row[0]),    # AppID
        clean_missing(row[1]),    # Name
        clean_missing(row[2]),    # Release date
        clean_missing(row[3]),    # Estimated owners
        clean_missing(row[4]),    # Peak CCU
        clean_missing(row[5]),    # Required age
        clean_missing(row[6]),    # Price
        clean_missing(row[7]),    # DiscountDLC count
        clean_missing(row[8]),    # About the game
        clean_missing(row[9]),    # Supported languages
        clean_missing(row[10]),   # Full audio languages
        clean_missing(row[11]),   # Reviews

        # Skip raw[12]

        clean_missing(row[13]),   # Header image
        clean_missing(row[14]),   # Website
        clean_missing(row[15]),   # Support url
        clean_missing(row[16]),   # Support email

        clean_missing(row[17]),   # Windows
        clean_missing(row[18]),   # Mac
        clean_missing(row[19]),   # Linux
        clean_missing(row[20]),   # Metacritic score
        clean_missing(row[21]),   # Metacritic url
        clean_missing(row[22]),   # User score
        clean_missing(row[23]),   # Positive
        clean_missing(row[24]),   # Negative
        clean_missing(row[25]),   # Score rank
        clean_missing(row[26]),   # Achievements
        clean_missing(row[27]),   # Recommendations
        clean_missing(row[28]),   # Notes
        clean_missing(row[29]),   # Average playtime forever
        clean_missing(row[30]),   # Average playtime two weeks
        clean_missing(row[31]),   # Median playtime forever
        clean_missing(row[32]),   # Median playtime two weeks
        clean_missing(row[33]),   # Developers
        clean_missing(row[34]),   # Publishers
        clean_missing(row[35]),   # Categories
        clean_missing(row[36]),   # Genres
        clean_missing(row[37]),   # Tags
        clean_missing(row[38]),   # Screenshots
        clean_missing(row[39]),   # Movies
    ]

    if len(cleaned) != EXPECTED_CLEAN_FIELDS:
        raise ValueError(
            f"Cleaned row has {len(cleaned)} fields "
            f"for AppID {row[0]}"
        )

    return cleaned


def main():

    print("=" * 80)
    print("STEAMSCOPE - REBUILD GAMES CLEANED CSV")
    print("=" * 80)

    print(f"Raw file    : {RAW_FILE}")
    print(f"Output file : {OUTPUT_FILE}")
    print()

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    total_rows = 0

    with open(
        RAW_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as infile:

        reader = csv.reader(infile)

        raw_header = next(reader)

        print(f"Raw header fields: {len(raw_header)}")

        if len(raw_header) != 39:
            raise ValueError(
                f"Expected 39 header fields, "
                f"got {len(raw_header)}"
            )

        with open(
            TEMP_FILE,
            "w",
            encoding="utf-8",
            newline=""
        ) as outfile:

            writer = csv.writer(outfile)

            writer.writerow(CLEANED_HEADER)

            for row in reader:

                total_rows += 1

                cleaned = transform_row(row)

                writer.writerow(cleaned)

                if total_rows % 10_000 == 0:
                    print(
                        f"Processed: {total_rows:,}"
                    )

    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)

    print(f"Rows processed: {total_rows:,}")

    if total_rows == 0:
        raise ValueError("No rows processed.")

    # ---------------------------------------------------------------
    # Validate the generated file
    # ---------------------------------------------------------------

    print()
    print("Checking generated CSV...")

    output_rows = 0

    with open(
        TEMP_FILE,
        "r",
        encoding="utf-8",
        newline=""
    ) as outfile:

        reader = csv.reader(outfile)

        header = next(reader)

        if len(header) != EXPECTED_CLEAN_FIELDS:
            raise ValueError(
                f"Output header has {len(header)} fields"
            )

        for row in reader:

            output_rows += 1

            if len(row) != EXPECTED_CLEAN_FIELDS:
                raise ValueError(
                    f"Output row {output_rows} has "
                    f"{len(row)} fields"
                )

    if output_rows != total_rows:
        raise ValueError(
            f"Input rows = {total_rows}, "
            f"output rows = {output_rows}"
        )

    print(
        f"Output rows: {output_rows:,}"
    )

    print()
    print("PASS: Raw rows contain 40 fields.")
    print("PASS: Cleaned header contains 39 fields.")
    print("PASS: Every cleaned row contains 39 fields.")
    print("PASS: Input/output row counts match.")

    # Replace old cleaned file only after successful validation.
    os.replace(
        TEMP_FILE,
        OUTPUT_FILE
    )

    print()
    print("=" * 80)
    print("REBUILD COMPLETE")
    print("=" * 80)

    print(
        f"Cleaned file: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()