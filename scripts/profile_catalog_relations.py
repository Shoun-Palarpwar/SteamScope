import pandas as pd

FILE = "data/cleaned/games_cleaned.csv"

COLUMNS = [
    "appid",
    "developers",
    "publishers",
    "genres",
    "tags",
    "categories",
    "supported_languages",
    "full_audio_languages",
    "screenshots",
]

df = pd.read_csv(
    FILE,
    usecols=COLUMNS,
    dtype=str,
    keep_default_na=False,
)

print("=" * 80)
print("STEAMSCOPE - CATALOG RELATION FIELD PROFILING")
print("=" * 80)
print(f"Rows: {len(df):,}")

for column in COLUMNS[1:]:
    non_empty = df[df[column].str.strip() != ""]

    print()
    print("=" * 80)
    print(f"[{column.upper()}]")
    print(f"Non-empty rows: {len(non_empty):,}")

    if len(non_empty) > 0:
        sample = non_empty.sample(
            min(5, len(non_empty)),
            random_state=42,
        )

        for _, row in sample.iterrows():
            print(f"\nAppID: {row['appid']}")
            print(f"{column}: {row[column]}")


print()
print("=" * 80)
print("PLATFORM DISTRIBUTION")
print("=" * 80)

platform_df = df[["appid"]].copy()

# Read platform columns separately because they are not in COLUMNS above
platforms = pd.read_csv(
    FILE,
    usecols=["windows", "mac", "linux"],
    dtype=str,
    keep_default_na=False,
)

print(
    platforms.value_counts().to_string()
)

print()
print("Profiling completed.")