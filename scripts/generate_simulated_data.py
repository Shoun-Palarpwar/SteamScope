"""
STEAMSCOPE - SIMULATED USER DATA GENERATOR

Generates fake but internally-consistent user-side data on top of
the real game catalog: users, library, wishlist, purchase,
achievement, user_achievement, user_activity.

None of this is real Steam data -- it's synthetic, generated to
populate the platform simulation side of the schema (per the
project's own design: "steamid in review is NOT a FK to user"
precisely because reviews are real public data and this user
layer is not).

Idempotent per table: skips any table that already has rows, so
it's safe to re-run after a partial failure.

Requires: mysql-connector-python (already used by load_games.py)
"""

import hashlib
import random
from datetime import datetime, timedelta

import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "steamscope",
}

N_USERS = 3000
LIBRARY_RANGE = (3, 60)
WISHLIST_RANGE = (0, 15)
EXTRA_REFUNDED_CANCELLED_RATE = 0.03
ACHIEVEMENTS_CAP_PER_GAME = 50
ACTIVITY_EVENTS_PER_LIBRARY_GAME = (1, 6)
BATCH_SIZE = 2000

RNG = random.Random(42)

PAYMENT_METHODS = ["Steam Wallet", "Credit Card", "PayPal", "Debit Card"]
ACTIVITY_TYPES = ["PLAY", "LAUNCH", "SESSION"]


def table_count(cursor, table):
    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
    return cursor.fetchone()[0]


def random_datetime(days_back=730):
    delta = timedelta(
        days=RNG.randint(0, days_back),
        seconds=RNG.randint(0, 86400),
    )
    return datetime.now() - delta


def fake_password_hash(seed):
    # Synthetic placeholder only -- not a real credential.
    return hashlib.sha256(f"steamscope_synthetic_{seed}".encode()).hexdigest()


def generate_users(cursor, connection):
    if table_count(cursor, "user") > 0:
        print("  user: already populated, skipping")
        cursor.execute("SELECT user_id FROM `user`")
        return [row[0] for row in cursor.fetchall()]

    rows = []
    for i in range(1, N_USERS + 1):
        username = f"player_{i:05d}"
        email = f"player_{i:05d}@steamscope.dev"
        rows.append((username, email, fake_password_hash(i)))

    insert_sql = "INSERT INTO `user` (username, email, password_hash) VALUES (%s, %s, %s)"
    for i in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(insert_sql, rows[i:i + BATCH_SIZE])
    connection.commit()

    cursor.execute("SELECT user_id FROM `user`")
    user_ids = [row[0] for row in cursor.fetchall()]
    print(f"  user: inserted {len(user_ids):,} users")
    return user_ids


POPULAR_FRACTION = 0.65
POPULAR_TIER_SIZE = 8000


def load_game_pool(cursor):
    cursor.execute(
        "SELECT app_id, price, achievement_count, positive_reviews FROM game"
    )
    games = cursor.fetchall()

    app_ids = [g[0] for g in games]
    price_map = {g[0]: (float(g[1]) if g[1] is not None else 0.0) for g in games}
    achievement_count_map = {g[0]: (g[2] or 0) for g in games}

    games_by_popularity = sorted(games, key=lambda g: (g[3] or 0), reverse=True)
    popular_app_ids = [g[0] for g in games_by_popularity[:POPULAR_TIER_SIZE]]

    return app_ids, popular_app_ids, price_map, achievement_count_map


def sample_library(app_ids, popular_app_ids, k):
    k = min(k, len(app_ids))
    n_popular = min(int(round(k * POPULAR_FRACTION)), len(popular_app_ids))
    n_rest = k - n_popular

    popular_pick = RNG.sample(popular_app_ids, n_popular)
    popular_set = set(popular_pick)

    rest_candidates = RNG.sample(app_ids, min(n_rest * 3 + 10, len(app_ids)))
    rest_pick = [a for a in rest_candidates if a not in popular_set][:n_rest]

    return popular_pick + rest_pick


def generate_library_wishlist_purchases(cursor, connection, user_ids, app_ids, popular_app_ids, price_map):
    if table_count(cursor, "library") > 0:
        print("  library/wishlist/purchase: already populated, skipping")
        return {}

    library_rows = []
    wishlist_rows = []
    purchase_rows = []
    user_library_map = {}

    for user_id in user_ids:
        lib_size = RNG.randint(*LIBRARY_RANGE)
        owned = sample_library(app_ids, popular_app_ids, lib_size)
        user_library_map[user_id] = owned

        for app_id in owned:
            added_at = random_datetime()
            library_rows.append((user_id, app_id, added_at))

            price = price_map.get(app_id, 0.0)
            purchase_rows.append(
                (user_id, app_id, added_at, price, RNG.choice(PAYMENT_METHODS), "COMPLETED")
            )

        if RNG.random() < EXTRA_REFUNDED_CANCELLED_RATE:
            extra_app = RNG.choice(app_ids)
            status = RNG.choice(["REFUNDED", "CANCELLED"])
            purchase_rows.append(
                (user_id, extra_app, random_datetime(), price_map.get(extra_app, 0.0),
                 RNG.choice(PAYMENT_METHODS), status)
            )

        wishlist_size = RNG.randint(*WISHLIST_RANGE)
        owned_set = set(owned)
        candidates = [a for a in RNG.sample(app_ids, min(wishlist_size * 3, len(app_ids)))
                      if a not in owned_set][:wishlist_size]
        for app_id in candidates:
            wishlist_rows.append((user_id, app_id, random_datetime()))

    lib_sql = "INSERT IGNORE INTO `library` (user_id, app_id, added_at) VALUES (%s, %s, %s)"
    wish_sql = "INSERT IGNORE INTO `wishlist` (user_id, app_id, added_at) VALUES (%s, %s, %s)"
    purch_sql = (
        "INSERT INTO `purchase` (user_id, app_id, purchase_date, price_paid, "
        "payment_method, transaction_status) VALUES (%s, %s, %s, %s, %s, %s)"
    )

    for rows, sql in [(library_rows, lib_sql), (wishlist_rows, wish_sql), (purchase_rows, purch_sql)]:
        for i in range(0, len(rows), BATCH_SIZE):
            cursor.executemany(sql, rows[i:i + BATCH_SIZE])
        connection.commit()

    print(f"  library: inserted {len(library_rows):,} rows")
    print(f"  wishlist: inserted {len(wishlist_rows):,} rows")
    print(f"  purchase: inserted {len(purchase_rows):,} rows")

    return user_library_map


def generate_achievements_and_progress(cursor, connection, user_library_map, achievement_count_map):
    if table_count(cursor, "achievement") > 0:
        print("  achievement/user_achievement: already populated, skipping")
        return

    games_needing_achievements = set()
    for owned in user_library_map.values():
        for app_id in owned:
            if achievement_count_map.get(app_id, 0) > 0:
                games_needing_achievements.add(app_id)

    achievement_rows = []
    for app_id in games_needing_achievements:
        n = min(achievement_count_map[app_id], ACHIEVEMENTS_CAP_PER_GAME)
        for i in range(1, n + 1):
            achievement_rows.append((app_id, f"Achievement {i}", None))

    insert_sql = "INSERT INTO achievement (app_id, name, description) VALUES (%s, %s, %s)"
    for i in range(0, len(achievement_rows), BATCH_SIZE):
        cursor.executemany(insert_sql, achievement_rows[i:i + BATCH_SIZE])
    connection.commit()
    print(f"  achievement: inserted {len(achievement_rows):,} rows "
          f"(across {len(games_needing_achievements):,} games)")

    cursor.execute("SELECT achievement_id, app_id FROM achievement")
    achievements_by_game = {}
    for achievement_id, app_id in cursor.fetchall():
        achievements_by_game.setdefault(app_id, []).append(achievement_id)

    user_achievement_rows = []
    for user_id, owned in user_library_map.items():
        for app_id in owned:
            options = achievements_by_game.get(app_id)
            if not options:
                continue
            unlocked_n = RNG.randint(0, len(options))
            for achievement_id in RNG.sample(options, unlocked_n):
                user_achievement_rows.append(
                    (user_id, achievement_id, random_datetime())
                )

    insert_sql = (
        "INSERT IGNORE INTO user_achievement (user_id, achievement_id, unlocked_at) "
        "VALUES (%s, %s, %s)"
    )
    for i in range(0, len(user_achievement_rows), BATCH_SIZE):
        cursor.executemany(insert_sql, user_achievement_rows[i:i + BATCH_SIZE])
    connection.commit()
    print(f"  user_achievement: inserted {len(user_achievement_rows):,} rows")


def generate_activity(cursor, connection, user_library_map):
    if table_count(cursor, "user_activity") > 0:
        print("  user_activity: already populated, skipping")
        return

    rows = []
    for user_id, owned in user_library_map.items():
        for app_id in owned:
            n_events = RNG.randint(*ACTIVITY_EVENTS_PER_LIBRARY_GAME)
            for _ in range(n_events):
                activity_type = RNG.choice(ACTIVITY_TYPES)
                duration = None if activity_type == "LAUNCH" else RNG.randint(5, 300)
                rows.append((user_id, app_id, activity_type, random_datetime(), duration))

    insert_sql = (
        "INSERT INTO user_activity (user_id, app_id, activity_type, activity_time, duration_minutes) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    for i in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(insert_sql, rows[i:i + BATCH_SIZE])
    connection.commit()
    print(f"  user_activity: inserted {len(rows):,} rows")


def main():
    print("=" * 70)
    print("STEAMSCOPE - SIMULATED USER DATA GENERATOR")
    print("=" * 70)

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    print("\nMySQL connection: PASS")

    try:
        game_count = table_count(cursor, "game")
        if game_count == 0:
            raise RuntimeError("game table is empty. Run load_games.py first.")
        print(f"game table rows: {game_count:,}")

        print("\n[1] Generating users...")
        user_ids = generate_users(cursor, connection)

        print("\n[2] Loading game pool for sampling...")
        app_ids, popular_app_ids, price_map, achievement_count_map = load_game_pool(cursor)
        print(f"  {len(app_ids):,} games available for simulation "
              f"({len(popular_app_ids):,} in the popular tier)")

        print("\n[3] Generating library / wishlist / purchase...")
        user_library_map = generate_library_wishlist_purchases(
            cursor, connection, user_ids, app_ids, popular_app_ids, price_map
        )
        if not any(user_library_map.values()):
            cursor.execute("SELECT user_id, app_id FROM `library`")
            user_library_map = {}
            for uid, aid in cursor.fetchall():
                user_library_map.setdefault(uid, []).append(aid)

        print("\n[4] Generating achievements + unlock progress...")
        generate_achievements_and_progress(cursor, connection, user_library_map, achievement_count_map)

        print("\n[5] Generating user activity...")
        generate_activity(cursor, connection, user_library_map)

        print("\n" + "=" * 70)
        print("PASS: Simulated user data generation completed.")
        print("=" * 70)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
