import csv
import mysql.connector

CSV_FILE = "data/cleaned/games_cleaned.csv"

# Use the SAME MySQL connection details
# that you used in scripts/load_games.py
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Carbon#oxide2@7",
    "database": "steamscope",
}


print("=" * 70)
print("STEAMSCOPE - GAME APPID COMPARISON")
print("=" * 70)

# ------------------------------------------------------------
# 1. Read AppIDs from cleaned CSV
# ------------------------------------------------------------

csv_appids = set()

with open(
    CSV_FILE,
    "r",
    encoding="utf-8",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:
        appid = row["AppID"].strip()

        if appid:
            csv_appids.add(int(appid))

print(f"CSV unique AppIDs : {len(csv_appids):,}")


# ------------------------------------------------------------
# 2. Read AppIDs from MySQL
# ------------------------------------------------------------

connection = mysql.connector.connect(**DB_CONFIG)

cursor = connection.cursor()

cursor.execute("""
    SELECT app_id
    FROM game
""")

db_appids = {
    int(row[0])
    for row in cursor.fetchall()
}

cursor.close()
connection.close()

print(f"DB unique AppIDs  : {len(db_appids):,}")


# ------------------------------------------------------------
# 3. Compare
# ------------------------------------------------------------

csv_not_db = sorted(csv_appids - db_appids)
db_not_csv = sorted(db_appids - csv_appids)

print()
print("=" * 70)
print("COMPARISON")
print("=" * 70)

print(f"CSV → DB missing : {len(csv_not_db)}")
print(f"DB → CSV missing : {len(db_not_csv)}")

print()

if csv_not_db:
    print("AppIDs present in CSV but NOT in MySQL:")
    for appid in csv_not_db:
        print(f"  {appid}")

if db_not_csv:
    print()
    print("AppIDs present in MySQL but NOT in CSV:")
    for appid in db_not_csv:
        print(f"  {appid}")

print()

if not csv_not_db and not db_not_csv:
    print("PASS: CSV and MySQL AppIDs match exactly.")
else:
    print("ATTENTION: AppID mismatch detected.")
