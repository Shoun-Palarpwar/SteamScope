"""
STEAMSCOPE API - USER ENDPOINTS

GET /users/{user_id}                profile (no password hash)
GET /users/{user_id}/library         owned games
GET /users/{user_id}/wishlist        wishlisted games
GET /users/{user_id}/achievements    unlocked achievements
GET /users/{user_id}/activity        recent play activity
"""

from fastapi import APIRouter, HTTPException, Query

from db import get_cursor

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


@router.get("/{user_id}")
def get_user(user_id: int):
    with get_cursor() as cur:
        return _require_user(cur, user_id)


@router.get("/{user_id}/library")
def get_library(user_id: int, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    with get_cursor() as cur:
        _require_user(cur, user_id)

        cur.execute("SELECT COUNT(*) AS total FROM library WHERE user_id = %s", (user_id,))
        total = cur.fetchone()["total"]

        cur.execute(
            """
            SELECT g.app_id, g.name, g.header_image_url, g.price, l.added_at
            FROM library l
            JOIN game g ON l.app_id = g.app_id
            WHERE l.user_id = %s
            ORDER BY l.added_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()

    return {"total": total, "limit": limit, "offset": offset, "results": rows}




@router.get("/{user_id}/wishlist")
def get_wishlist(user_id: int, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    with get_cursor() as cur:
        _require_user(cur, user_id)

        cur.execute("SELECT COUNT(*) AS total FROM wishlist WHERE user_id = %s", (user_id,))
        total = cur.fetchone()["total"]

        cur.execute(
            """
            SELECT g.app_id, g.name, g.header_image_url, g.price, w.added_at
            FROM wishlist w
            JOIN game g ON w.app_id = g.app_id
            WHERE w.user_id = %s
            ORDER BY w.added_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()

    return {"total": total, "limit": limit, "offset": offset, "results": rows}


@router.get("/{user_id}/achievements")
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
            ORDER BY ua.unlocked_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()

    return {"total": total, "limit": limit, "offset": offset, "results": rows}


@router.get("/{user_id}/activity")
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
            ORDER BY ua.activity_time DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )
        rows = cur.fetchall()

    return {"total": total, "limit": limit, "offset": offset, "results": rows}
