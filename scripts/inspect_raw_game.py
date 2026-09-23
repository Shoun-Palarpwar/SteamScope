import csv
from collections import Counter

FILE = "data/raw/games.csv"

patterns = Counter()
examples = {}

with open(FILE, "r", encoding="utf-8", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)

    for row in reader:
        if len(row) != 40:
            continue

        support_url = row[15].strip()
        position_16 = row[16].strip()

        if support_url == "":
            url_type = "EMPTY"
        elif support_url.startswith(("http://", "https://")):
            url_type = "URL"
        else:
            url_type = "OTHER"

        if position_16 == "":
            email_type = "EMPTY"
        elif "@" in position_16:
            email_type = "EMAIL"
        elif position_16.lower() in ("true", "false"):
            email_type = "BOOLEAN"
        else:
            email_type = "OTHER"

        pattern = (url_type, email_type)
        patterns[pattern] += 1

        if pattern not in examples:
            examples[pattern] = (
                row[0],
                row[1],
                support_url,
                position_16,
                row[17],
                row[18],
                row[19],
            )

print("=" * 90)
print("SUPPORT URL / SUPPORT EMAIL STRUCTURE")
print("=" * 90)

print(f"Total patterns: {len(patterns)}")
print()

for pattern, count in patterns.most_common():
    print(f"{count:8,} rows | URL={pattern[0]:<6} | POS16={pattern[1]:<7}")

    appid, name, url, pos16, windows, mac, linux = examples[pattern]

    print(f"           Example AppID : {appid}")
    print(f"           Name          : {name[:60]}")
    print(f"           Position 15   : {url[:100]!r}")
    print(f"           Position 16   : {pos16[:100]!r}")
    print(f"           Next fields   : {windows!r}, {mac!r}, {linux!r}")
    print()