from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, StrictBool
from ..db import get_cursor
from .users import _require_user
from ..collection_queries import collection_page, CollectionSort, SortOrder
from ..schemas import Profiles, FavoriteState, Page, CollectionCard

router = APIRouter()

class FavoriteUpdate(BaseModel):
    is_favorite: StrictBool


def require_game(cur, app_id):
    cur.execute('SELECT app_id FROM game WHERE app_id = %s', (app_id,))
    if not cur.fetchone():
        raise HTTPException(404, 'Game not found')


@router.get('', response_model=Profiles)
def profiles(search: str = Query('', max_length=100), limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0)):
    with get_cursor() as cur:
        cur.execute('SELECT COUNT(*) AS total FROM `user` WHERE username LIKE %s', (f'%{search}%',))
        total = cur.fetchone()['total']
        cur.execute('SELECT user_id, username FROM `user` WHERE username LIKE %s ORDER BY user_id LIMIT %s OFFSET %s', (f'%{search}%', limit, offset))
        rows = cur.fetchall()
    return dict(total=total, limit=limit, offset=offset, results=rows, data_source='simulated')


def edit_collection(user_id, app_id, collection, add):
    # Serialize collection edits per profile, including library/wishlist transitions.
    with get_cursor() as cur:
        _require_user(cur, user_id)
        cur.execute('SELECT user_id FROM `user` WHERE user_id=%s FOR UPDATE', (user_id,))
        cur.fetchone()
        require_game(cur, app_id)
        if add:
            if collection == 'wishlist':
                cur.execute('SELECT 1 FROM `library` WHERE user_id=%s AND app_id=%s', (user_id, app_id))
                if cur.fetchone():
                    raise HTTPException(409, 'Owned games cannot be wishlisted')
            cur.execute(f'INSERT INTO `{collection}` (user_id, app_id) VALUES (%s,%s) ON DUPLICATE KEY UPDATE app_id=app_id', (user_id, app_id))
            if collection == 'library':
                cur.execute('DELETE FROM wishlist WHERE user_id=%s AND app_id=%s', (user_id, app_id))
        else:
            cur.execute(f'DELETE FROM `{collection}` WHERE user_id=%s AND app_id=%s', (user_id, app_id))
    return Response(status_code=204)


@router.put('/{user_id}/library/{app_id}', status_code=204)
def add_owned(user_id: int, app_id: int):
    return edit_collection(user_id, app_id, 'library', True)


@router.delete('/{user_id}/library/{app_id}', status_code=204)
def remove_owned(user_id: int, app_id: int):
    return edit_collection(user_id, app_id, 'library', False)


@router.put('/{user_id}/wishlist/{app_id}', status_code=204)
def add_wishlist(user_id: int, app_id: int):
    return edit_collection(user_id, app_id, 'wishlist', True)


@router.delete('/{user_id}/wishlist/{app_id}', status_code=204)
def remove_wishlist(user_id: int, app_id: int):
    return edit_collection(user_id, app_id, 'wishlist', False)


@router.patch('/{user_id}/library/{app_id}/favorite', response_model=FavoriteState)
def set_favorite(user_id: int, app_id: int, body: FavoriteUpdate):
    with get_cursor() as cur:
        _require_user(cur, user_id)
        cur.execute('SELECT user_id FROM `user` WHERE user_id=%s FOR UPDATE', (user_id,))
        cur.fetchone()
        cur.execute('SELECT app_id FROM `library` WHERE user_id=%s AND app_id=%s', (user_id, app_id))
        if not cur.fetchone():
            raise HTTPException(404, 'Game is not in this library')
        cur.execute('UPDATE `library` SET is_favorite=%s WHERE user_id=%s AND app_id=%s', (body.is_favorite, user_id, app_id))
    return dict(user_id=user_id, app_id=app_id, is_favorite=body.is_favorite)


@router.get('/{user_id}/favorites', response_model=Page[CollectionCard])
def favorites(user_id: int, limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0),
              search: str = Query('', max_length=200), sort_by: CollectionSort = 'added_at',
              order: SortOrder = 'desc'):
    with get_cursor() as cur:
        _require_user(cur, user_id)
        return collection_page(cur, user_id, 'favorites', search, sort_by, order, limit, offset)
