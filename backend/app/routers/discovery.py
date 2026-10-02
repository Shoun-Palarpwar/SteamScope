from fastapi import APIRouter, Query, HTTPException
from ..db import get_cursor
from .users import _require_user
from .collections import require_game
from ..cards import enrich_cards
from ..schemas import Page, FilterOption, Recommendations

router = APIRouter()
RELATIONS = {'genre': ('genre', 'genre_id'), 'tag': ('tag', 'tag_id'),
             'developer': ('developer', 'developer_id'), 'publisher': ('publisher', 'publisher_id'),
             'category': ('category', 'category_id'), 'platform': ('platform', 'platform_id'),
             'language': ('language', 'language_id')}
SIGNALS = [('tag', 'tag_id', 3), ('genre', 'genre_id', 1), ('developer', 'developer_id', 2)]


@router.get('/filters/{kind}', response_model=Page[FilterOption])
def filters(kind: str, search: str = Query('', max_length=100), limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    if kind not in RELATIONS:
        raise HTTPException(422, f'kind must be one of {list(RELATIONS)}')
    table, key = RELATIONS[kind]
    with get_cursor() as cur:
        cur.execute(f'SELECT COUNT(*) AS total FROM `{table}` WHERE name LIKE %s', (f'%{search}%',))
        total = cur.fetchone()['total']
        cur.execute(f'SELECT {key} AS id, name FROM `{table}` WHERE name LIKE %s ORDER BY name, {key} LIMIT %s OFFSET %s', (f'%{search}%', limit, offset))
        rows = cur.fetchall()
    return dict(total=total, limit=limit, offset=offset, results=rows)


def recommend(cur, limit, user_id=None, app_id=None, viewer_id=None):
    if user_id is not None:
        seeds = 'SELECT app_id, IF(is_favorite, 3, 1) AS weight FROM `library` WHERE user_id=%s'
        seed_params = [user_id]
        exclusion = 'NOT EXISTS (SELECT 1 FROM `library` owned WHERE owned.user_id=%s AND owned.app_id=g.app_id)'
        exclude_params = [user_id]
    else:
        seeds = 'SELECT app_id, 1 AS weight FROM game WHERE app_id=%s'
        seed_params = [app_id]
        exclusion = 'g.app_id <> %s'
        exclude_params = [app_id]
    # Independent attribute aggregation avoids multiplicative genre/tag/developer joins.
    ctes = [f'seeds AS ({seeds})']
    parts = []
    for kind, key, factor in SIGNALS:
        ctes.append(f'''pref_{kind} AS (
            SELECT r.{key}, SUM(s.weight) AS weight FROM game_{kind} r
            JOIN seeds s ON s.app_id=r.app_id GROUP BY r.{key})''')
        parts.append(f'''SELECT r.app_id, SUM(p.weight)*{factor} AS score
            FROM game_{kind} r JOIN pref_{kind} p ON p.{key}=r.{key} GROUP BY r.app_id''')
    ctes.append('signals AS (' + ' UNION ALL '.join(parts) + ')')
    ctes.append('scores AS (SELECT app_id, SUM(score) AS match_score FROM signals GROUP BY app_id)')
    cur.execute('WITH ' + ','.join(ctes) + f'''
        SELECT g.app_id,g.name,g.header_image_url,g.positive_reviews,s.match_score
        FROM scores s JOIN game g ON g.app_id=s.app_id WHERE {exclusion}
        ORDER BY s.match_score DESC, COALESCE(g.positive_reviews,0) DESC, g.app_id LIMIT %s''', seed_params + exclude_params + [limit])
    rows = cur.fetchall()
    fallback = not rows
    if fallback:
        cur.execute(f'''SELECT g.app_id,g.name,g.header_image_url,g.positive_reviews,0 AS match_score
            FROM game g WHERE {exclusion}
            ORDER BY COALESCE(g.positive_reviews,0) DESC,g.app_id LIMIT %s''', exclude_params + [limit])
        rows = cur.fetchall()
    for row in rows:
        row['reasons'] = []
    if rows and not fallback:
        ids = [r['app_id'] for r in rows]
        placeholders = ','.join(['%s'] * len(ids))
        by_id = {r['app_id']:r for r in rows}
        for kind, key, factor in SIGNALS:
            cur.execute(f'''WITH seeds AS ({seeds})
                SELECT candidate.app_id, attribute.name AS attribute, source.app_id AS source_app_id,
                       source.name AS source_game, s.weight AS source_weight
                FROM game_{kind} candidate
                JOIN game_{kind} shared ON shared.{key}=candidate.{key}
                JOIN seeds s ON s.app_id=shared.app_id
                JOIN game source ON source.app_id=s.app_id
                JOIN `{kind}` attribute ON attribute.{key}=candidate.{key}
                WHERE candidate.app_id IN ({placeholders})
                ORDER BY candidate.app_id,s.weight DESC,source.app_id,attribute.name''', seed_params + ids)
            for reason in cur.fetchall():
                dest = by_id[reason.pop('app_id')]['reasons']
                # Limit explanation payload, not scoring inputs.
                if sum(r['type'] == kind for r in dest) < 3:
                    dest.append(dict(type=kind, **reason))
    enrich_cards(cur, rows, user_id if user_id is not None else viewer_id)
    return dict(strategy='popular_fallback' if fallback else 'attribute_overlap',
        scoring={'tag':3,'genre':1,'developer':2,'favorite_multiplier':3,
                 'popularity':'positive_reviews breaks match-score ties'}, results=rows)


@router.get('/games/{app_id}/similar', response_model=Recommendations)
def similar(app_id: int, limit: int = Query(12, ge=1, le=50),
            user_id: int | None = Query(None, gt=0)):
    with get_cursor() as cur:
        if user_id is not None:
            _require_user(cur, user_id)
        require_game(cur, app_id)
        return recommend(cur, limit, app_id=app_id, viewer_id=user_id)


@router.get('/users/{user_id}/recommendations', response_model=Recommendations)
def recommendations(user_id: int, limit: int = Query(12, ge=1, le=50)):
    with get_cursor() as cur:
        _require_user(cur, user_id)
        return recommend(cur, limit, user_id=user_id)
