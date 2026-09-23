import csv
from datetime import datetime
from pathlib import Path

import mysql.connector


# ============================================================
# STEAMSCOPE - GAME CATALOG ETL
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_FILE = BASE_DIR / "data" / "cleaned" / "games_cleaned.csv"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "steamscope",
}

BATCH_SIZE = 2000


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return None

    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return None

    return value


def clean_int(value):
    value = clean_text(value)

    if value is None:
        return None

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def clean_decimal(value):
    value = clean_text(value)

    if value is None:
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def clean_date(value):
    value = clean_text(value)

    if value is None:
        return None

    formats = [
        "%Y-%m-%d",
        "%b %d, %Y",
        "%B %d, %Y",
        "%b %Y",
        "%B %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    return None


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("STEAMSCOPE - GAME CATALOG ETL")
    print("=" * 70)

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {CSV_FILE}"
        )

    print(f"\nDataset: {CSV_FILE}")
    print(f"Batch size: {BATCH_SIZE:,}")

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    print("\n[1] Connecting to MySQL...")

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    print("MySQL connection: PASS")

    try:

        # ----------------------------------------------------
        # CHECK EXISTING DATA
        # ----------------------------------------------------

        cursor.execute("SELECT COUNT(*) FROM game")
        existing_count = cursor.fetchone()[0]

        print(f"Existing GAME rows: {existing_count:,}")

        if existing_count != 0:
            raise RuntimeError(
                "GAME table is not empty. "
                "ETL stopped to prevent duplicate data."
            )

        # ----------------------------------------------------
        # SQL
        # ----------------------------------------------------

        game_sql = """
            INSERT INTO game (
                app_id,
                name,
                release_date,
                estimated_owners,
                peak_ccu,
                required_age,
                price,
                discount_dlc_count,
                description,
                header_image_url,
                website_url,
                support_url,
                support_email,
                metacritic_score,
                metacritic_url,
                user_score,
                positive_reviews,
                negative_reviews,
                score_rank,
                achievement_count,
                recommendation_count,
                notes,
                avg_playtime_forever,
                avg_playtime_2weeks,
                median_playtime_forever,
                median_playtime_2weeks
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s
            )
        """

        # ----------------------------------------------------
        # START TRANSACTION
        # ----------------------------------------------------

        print(f"\n[2] Starting GAME import...")

        # Count the actual rows in the cleaned dataset once so the
        # validation matches the current source instead of a stale
        # hard-coded value from an older extraction.
        expected_csv_rows = 0
        with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as file:
            expected_csv_rows = sum(1 for _ in csv.DictReader(file))

        print(f"Expected CSV rows: {expected_csv_rows:,}")

        batch = []
        total_read = 0
        total_inserted = 0
        invalid_dates = 0

        # ----------------------------------------------------
        # STREAM CSV
        # ----------------------------------------------------

        with open(
            CSV_FILE,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            expected_columns = {
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
            }

            missing_columns = expected_columns - set(reader.fieldnames or [])

            if missing_columns:
                raise RuntimeError(
                    f"Missing CSV columns: {missing_columns}"
                )

            for row in reader:

                total_read += 1

                app_id = clean_int(row["appid"])
                name = clean_text(row["name"])

                # Required GAME fields
                if app_id is None:
                    raise ValueError(
                        f"Invalid AppID at CSV row {total_read + 1}"
                    )

                if name is None:
                    raise ValueError(
                        f"NULL/empty game name at CSV row {total_read + 1}, "
                        f"AppID={app_id}"
                    )

                release_date = clean_date(row["release_date"])

                if (
                    clean_text(row["release_date"]) is not None
                    and release_date is None
                ):
                    invalid_dates += 1

                batch.append(
                    (
                        app_id,
                        name,
                        release_date,
                        clean_text(row["estimated_owners"]),
                        clean_int(row["peak_ccu"]),
                        clean_int(row["required_age"]),
                        clean_decimal(row["price"]),
                        clean_int(row["discountdlc_count"]),
                        clean_text(row["about_the_game"]),
                        clean_text(row["header_image"]),
                        clean_text(row["website"]),
                        clean_text(row["support_url"]),
                        clean_text(row["support_email"]),
                        clean_int(row["metacritic_score"]),
                        clean_text(row["metacritic_url"]),
                        clean_decimal(row["user_score"]),
                        clean_int(row["positive"]),
                        clean_int(row["negative"]),
                        clean_int(row["score_rank"]),
                        clean_int(row["achievements"]),
                        clean_int(row["recommendations"]),
                        clean_text(row["notes"]),
                        clean_int(row["average_playtime_forever"]),
                        clean_int(row["average_playtime_two_weeks"]),
                        clean_int(row["median_playtime_forever"]),
                        clean_int(row["median_playtime_two_weeks"]),
                    )
                )

                # ------------------------------------------------
                # INSERT BATCH
                # ------------------------------------------------

                if len(batch) >= BATCH_SIZE:

                    cursor.executemany(
                        game_sql,
                        batch
                    )

                    total_inserted += len(batch)
                    batch.clear()

                    print(
                        f"Inserted: {total_inserted:,} / 125,854",
                        end="\r"
                    )

            # ----------------------------------------------------
            # FINAL BATCH
            # ----------------------------------------------------

            if batch:

                cursor.executemany(
                    game_sql,
                    batch
                )

                total_inserted += len(batch)
                batch.clear()

        print()
        print(f"\nCSV rows read: {total_read:,}")
        print(f"GAME rows inserted: {total_inserted:,}")
        print(f"Unparseable dates: {invalid_dates:,}")

        # ----------------------------------------------------
        # VERIFY BEFORE COMMIT
        # ----------------------------------------------------

        cursor.execute("SELECT COUNT(*) FROM game")
        db_count = cursor.fetchone()[0]

        print(f"GAME rows before commit: {db_count:,}")

        if total_read != expected_csv_rows:
            raise RuntimeError(
                f"Expected {expected_csv_rows:,} CSV rows, found {total_read:,}"
            )

        if total_inserted != expected_csv_rows:
            raise RuntimeError(
                f"Expected {expected_csv_rows:,} inserted rows, "
                f"found {total_inserted:,}"
            )

        if db_count != expected_csv_rows:
            raise RuntimeError(
                f"Database count mismatch: {db_count:,}"
            )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        connection.commit()

        print("\nTransaction committed successfully.")

        # ----------------------------------------------------
        # FINAL VERIFICATION
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_games,
                COUNT(DISTINCT app_id) AS unique_appids,
                COUNT(name) AS non_null_names,
                COUNT(release_date) AS non_null_dates
            FROM game
            """
        )

        total_games, unique_appids, names, dates = cursor.fetchone()

        print("\n" + "=" * 70)
        print("FINAL GAME TABLE VERIFICATION")
        print("=" * 70)

        print(f"Total games    : {total_games:,}")
        print(f"Unique AppIDs  : {unique_appids:,}")
        print(f"Non-null names : {names:,}")
        print(f"Non-null dates : {dates:,}")

        if total_games != expected_csv_rows:
            raise RuntimeError("Incorrect GAME count.")

        if unique_appids != expected_csv_rows:
            raise RuntimeError("Duplicate AppIDs detected.")

        if names != expected_csv_rows:
            raise RuntimeError("Some GAME names are NULL.")

        print("\nPASS: GAME ETL completed successfully.")

    except Exception as error:

        connection.rollback()

        print("\n\nERROR:")
        print(error)
        print("\nTransaction rolled back.")

        raise

    finally:

        cursor.close()
        connection.close()

        print("\nMySQL connection closed.")


if __name__ == "__main__":
    main()