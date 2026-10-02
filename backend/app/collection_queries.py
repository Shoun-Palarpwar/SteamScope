from typing import Literal

from .cards import enrich_cards

CollectionSort = Literal['added_at', 'name']
SortOrder = Literal['asc', 'desc']


def collection_page(cur, user_id, collection, search, sort_by, order, limit, offset):
    table = 'wishlist' if collection == 'wishlist' else 'library'
    condition = 'c.user_id=%s'
    params = [user_id]
    if collection == 'favorites':
        condition += ' AND c.is_favorite=TRUE'
    if search:
        condition += ' AND g.name LIKE %s'
        params.append(f'%{search}%')
    joins = f'FROM `{table}` c JOIN game g ON g.app_id=c.app_id'
    cur.execute(f'SELECT COUNT(*) AS total {joins} WHERE {condition}', params)
    total = cur.fetchone()['total']
    column = {'added_at': 'c.added_at', 'name': 'g.name'}[sort_by]
    direction = {'asc': 'ASC', 'desc': 'DESC'}[order]
    cur.execute(f'''SELECT g.app_id, c.added_at {joins} WHERE {condition}
        ORDER BY {column} {direction}, g.app_id ASC LIMIT %s OFFSET %s''', params + [limit, offset])
    rows = enrich_cards(cur, cur.fetchall(), user_id)
    return dict(total=total, limit=limit, offset=offset, results=rows)
