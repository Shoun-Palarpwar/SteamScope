from datetime import date, timedelta
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from ..db import get_cursor
from ..cards import enrich_cards
from ..schemas import Rankings
from .users import _require_user

router = APIRouter()
STEAM = {'peak_ccu':'Recorded peak concurrent players',
         'positive_reviews':'Positive review count', 'recommendation_count':'Recommendation count'}
COMMUNITY = {'owners':'Demo profiles owning the game',
             'active_players':'Distinct demo profiles with PLAY or SESSION events',
             'play_minutes':'Sum of recorded PLAY and SESSION duration in minutes'}


@router.get('/rankings', response_model=Rankings)
def rankings(source: Literal['steam','community'] = 'steam', metric: str = 'peak_ccu',
             start_date: date | None = None, end_date: date | None = None,
             limit: int = Query(20, ge=1, le=100), user_id: int | None = Query(None, gt=0)):
    allowed = STEAM if source == 'steam' else COMMUNITY
    if metric not in allowed:
        raise HTTPException(422, f'Metric for {source} must be one of {list(allowed)}')
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, 'start_date must not exceed end_date')
    if end_date == date.max:
        raise HTTPException(422, 'end_date must be earlier than 9999-12-31')
    if (start_date or end_date) and (source == 'steam' or metric == 'owners'):
        raise HTTPException(422, 'Date filters apply only to community activity metrics')
    params = []
    activity_range = None
    with get_cursor() as cur:
        if user_id is not None:
            _require_user(cur, user_id)
        if source == 'steam':
            query = f'''SELECT app_id,name,header_image_url,{metric} AS metric_value
                FROM game WHERE {metric} IS NOT NULL ORDER BY {metric} DESC,app_id LIMIT %s'''
        elif metric == 'owners':
            query = '''SELECT g.app_id,g.name,g.header_image_url,COUNT(*) AS metric_value
                FROM `library` l JOIN game g ON g.app_id=l.app_id
                GROUP BY g.app_id,g.name,g.header_image_url ORDER BY metric_value DESC,g.app_id LIMIT %s'''
        else:
            cur.execute("SELECT MIN(activity_time) AS first_event,MAX(activity_time) AS last_event FROM user_activity WHERE activity_type IN ('PLAY','SESSION')")
            activity_range = cur.fetchone()
            conditions = ["a.activity_type IN ('PLAY','SESSION')"]
            if start_date:
                conditions.append('a.activity_time >= %s')
                params.append(start_date)
            if end_date:
                conditions.append('a.activity_time < %s')
                params.append(end_date + timedelta(days=1))
            aggregate = 'COUNT(DISTINCT a.user_id)' if metric == 'active_players' else 'SUM(COALESCE(a.duration_minutes,0))'
            query = f'''SELECT g.app_id,g.name,g.header_image_url,{aggregate} AS metric_value
                FROM user_activity a JOIN game g ON g.app_id=a.app_id WHERE {' AND '.join(conditions)}
                GROUP BY g.app_id,g.name,g.header_image_url ORDER BY metric_value DESC,g.app_id LIMIT %s'''
        cur.execute(query, params + [limit])
        rows = enrich_cards(cur, cur.fetchall(), user_id)
    return dict(source=source, simulated=source=='community', live=False, metric=metric,
                definition=allowed[metric], start_date=start_date, end_date=end_date,
                date_semantics='Inclusive dates in stored database time; omitted bounds are unbounded',
                activity_range=activity_range, results=rows)
