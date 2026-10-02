"""Batch-load card fields for the current page without per-game queries."""


def enrich_cards(cur, rows, user_id=None):
    if not rows:
        return rows
    placeholders = ','.join(['%s'] * len(rows))
    ids = [row['app_id'] for row in rows]
    cur.execute(f'''SELECT app_id, name, header_image_url, release_date, price,
        positive_reviews, negative_reviews, metacritic_score, recommendation_count, peak_ccu
        FROM game WHERE app_id IN ({placeholders})''', ids)
    cards = {row['app_id']: dict(row, genres=[], is_owned=None,
                               is_wishlisted=None, is_favorite=None) for row in cur.fetchall()}
    cur.execute(f'''SELECT j.app_id, g.name FROM game_genre j
        JOIN genre g ON g.genre_id=j.genre_id WHERE j.app_id IN ({placeholders})
        ORDER BY g.name, g.genre_id''', ids)
    for genre in cur.fetchall():
        cards[genre['app_id']]['genres'].append(genre['name'])
    if user_id is not None:
        for card in cards.values():
            card.update(is_owned=False, is_wishlisted=False, is_favorite=False)
        cur.execute(f'''SELECT app_id, is_favorite FROM `library`
            WHERE user_id=%s AND app_id IN ({placeholders})''', [user_id] + ids)
        for owned in cur.fetchall():
            cards[owned['app_id']].update(is_owned=True, is_favorite=bool(owned['is_favorite']))
        cur.execute(f'''SELECT app_id FROM wishlist
            WHERE user_id=%s AND app_id IN ({placeholders})''', [user_id] + ids)
        for wished in cur.fetchall():
            cards[wished['app_id']]['is_wishlisted'] = True
    for row in rows:
        row.update(cards[row['app_id']])
    return rows
