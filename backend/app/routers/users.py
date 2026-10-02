"""
STEAMSCOPE API - USER ENDPOINTS

GET /users/{user_id}                profile (no password hash)
GET /users/{user_id}/library         owned games
GET /users/{user_id}/wishlist        wishlisted games
GET /users/{user_id}/achievements    unlocked achievements
GET /users/{user_id}/activity        recent play activity
"""

from fastapi import APIRouter, HTTPException, Query

from ..db import get_cursor
from ..collection_queries import collection_page, CollectionSort, SortOrder
from ..schemas import Page, CollectionCard, Profile, ProfileSummary, Achievement, Activity

router = APIRouter()


def _require_user(cur, user_id):
    cur.execute(
        "SELECT user_id, username, created_at FROM `user` WHERE user_id = %s",
        (user_id,),
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(404, f"User {user_id} not found")
    return user


@router.get("/{user_id}", response_model=Profile)
def get_user(user_id: int):
    with get_cursor() as cur:
        return _require_user(cur, user_id)


@router.get("/{user_id}/summary", response_model=ProfileSummary)
def get_summary(user_id: int):
    with get_cursor() as cur:
        profile = _require_user(cur, user_id)
        cur.execute('''SELECT COUNT(*) AS library_count,
            COALESCE(SUM(is_favorite=TRUE),0) AS favorite_count
            FROM `library` WHERE user_id=%s''', (user_id,))
        profile.update(cur.fetchone())
        cur.execute('SELECT COUNT(*) AS wishlist_count FROM wishlist WHERE user_id=%s', (user_id,))
        profile.update(cur.fetchone())
    return dict(profile, data_source='simulated')


@router.get("/{user_id}/library", response_model=Page[CollectionCard])
def get_library(user_id: int, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                search: str = Query('', max_length=200), sort_by: CollectionSort = 'added_at',
                order: SortOrder = 'desc'):
    with get_cursor() as cur:
        _require_user(cur, user_id)
        return collection_page(cur, user_id, 'library', search, sort_by, order, limit, offset)


@router.get("/{user_id}/wishlist", response_model=Page[CollectionCard])
def get_wishlist(user_id: int, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                 search: str = Query('', max_length=200), sort_by: CollectionSort = 'added_at',
                 order: SortOrder = 'desc'):
    with get_cursor() as cur:
        _require_user(cur, user_id)
        return collection_page(cur, user_id, 'wishlist', search, sort_by, order, limit, offset)


@router.get("/{user_id}/achievements", response_model=Page[Achievement])
def get_achievements(user_id: int, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    with get_cursor() as cur:
        _require_user(cur, user_id)

        cur.execute(
            "SELECT COUNT(*) AS total FROM user_achievement WHERE user_id = %s", (user_id,)
        )
        total = cur.fetchone()["total"]

        cur.execute(
            """
            SELECT g.app_id, g.name AS game_name, a.name AS achievement_name,
                   ua.unlocked_at
            FROM user_achievement ua
            JOIN achievement a ON ua.achievement_id = a.achievement_id
            JOIN game g ON a.app_id = g.app_id
            WHERE ua.user_id = %s
            ORDER BY ua.unlocked_at DESC, ua.achievement_id
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()

    return {"total": total, "limit": limit, "offset": offset, "results": rows}


@router.get("/{user_id}/activity", response_model=Page[Activity])
def get_activity(user_id: int, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    with get_cursor() as cur:
        _require_user(cur, user_id)

        cur.execute(
            "SELECT COUNT(*) AS total FROM user_activity WHERE user_id = %s", (user_id,)
        )
        total = cur.fetchone()["total"]

        cur.execute(
            """
            SELECT g.app_id, g.name AS game_name, ua.activity_type,
                   ua.activity_time, ua.duration_minutes
            FROM user_activity ua
            JOIN game g ON ua.app_id = g.app_id
            WHERE ua.user_id = %s
            ORDER BY ua.activity_time DESC, ua.activity_id
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()

    return {"total": total, "limit": limit, "offset": offset, "results": rows}
