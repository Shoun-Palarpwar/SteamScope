"""
STEAMSCOPE API - GAME CATALOG ENDPOINTS

GET /games            list, with search/filter/sort/pagination
GET /games/{app_id}    single game detail, with all its relationships
"""

from fastapi import APIRouter, HTTPException, Query

from db import get_cursor

router = APIRouter()

SORTABLE_COLUMNS = {
    "name": "g.name",
    "release_date": "g.release_date",
    "price": "g.price",
    "positive_reviews": "g.positive_reviews",
    "metacritic_score": "g.metacritic_score",
    "recommendation_count": "g.recommendation_count",
    "peak_ccu": "g.peak_ccu",
}


@router.get("")
def list_games(
    search: str | None = Query(None, description="Search by name"),
    genre: str | None = Query(None, description="Filter by exact genre name"),
    tag: str | None = Query(None, description="Filter by exact tag name"),
    category: str | None = Query(None, description="Filter by exact category name"),
    platform: str | None = Query(None, description="Filter by exact platform name (Windows/Mac/Linux)"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    sort_by: str = Query("positive_reviews", description=f"One of: {', '.join(SORTABLE_COLUMNS)}"),
    order: str = Query("desc", pattern="^(?i)(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    if sort_by not in SORTABLE_COLUMNS:
        raise HTTPException(400, f"sort_by must be one of: {', '.join(SORTABLE_COLUMNS)}")

    where_clauses = []
    params: list = []

    if search:
        where_clauses.append("g.name LIKE %s")
        params.append(f"%{search}%")

    if genre:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM game_genre gg JOIN genre gr ON gg.genre_id = gr.genre_id "
            "WHERE gg.app_id = g.app_id AND gr.name = %s)"
        )
        params.append(genre)

    if tag:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM game_tag gt JOIN tag t ON gt.tag_id = t.tag_id "
            "WHERE gt.app_id = g.app_id AND t.name = %s)"
        )
        params.append(tag)

    if category:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM game_category gc JOIN category c ON gc.category_id = c.category_id "
            "WHERE gc.app_id = g.app_id AND c.name = %s)"
        )
        params.append(category)

    if platform:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM game_platform gp JOIN platform p ON gp.platform_id = p.platform_id "
            "WHERE gp.app_id = g.app_id AND p.name = %s)"
        )
        params.append(platform)

    if min_price is not None:
        where_clauses.append("g.price >= %s")
        params.append(min_price)

    if max_price is not None:
        where_clauses.append("g.price <= %s")
        params.append(max_price)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    order_sql = "DESC" if order.lower() == "desc" else "ASC"
    sort_col = SORTABLE_COLUMNS[sort_by]

    query = f"""
        SELECT g.app_id, g.name, g.release_date, g.price, g.header_image_url,
               g.metacritic_score, g.positive_reviews, g.negative_reviews,
               g.recommendation_count, g.peak_ccu
        FROM game g
        {where_sql}
        ORDER BY {sort_col} {order_sql}
        LIMIT %s OFFSET %s
    """
    params += [limit, offset]

    count_query = f"SELECT COUNT(*) AS total FROM game g {where_sql}"

    with get_cursor() as cur:
        cur.execute(count_query, params[:-2] if where_clauses else [])
        total = cur.fetchone()["total"]

        cur.execute(query, params)
        rows = cur.fetchall()

    return {"total": total, "limit": limit, "offset": offset, "results": rows}


@router.get("/{app_id}")
def get_game_detail(app_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM game WHERE app_id = %s", (app_id,))
        game = cur.fetchone()

        if not game:
            raise HTTPException(404, f"Game {app_id} not found")

        def fetch_names(junction_table, lookup_table, id_col):
            cur.execute(
                f"""
                SELECT l.name FROM {junction_table} j
                JOIN {lookup_table} l ON j.{id_col} = l.{id_col}
                WHERE j.app_id = %s
                """,
                (app_id,),
            )
            return [row["name"] for row in cur.fetchall()]

        game["developers"] = fetch_names("game_developer", "developer", "developer_id")
        game["publishers"] = fetch_names("game_publisher", "publisher", "publisher_id")
        game["genres"] = fetch_names("game_genre", "genre", "genre_id")
        game["tags"] = fetch_names("game_tag", "tag", "tag_id")
        game["categories"] = fetch_names("game_category", "category", "category_id")
        game["platforms"] = fetch_names("game_platform", "platform", "platform_id")

        cur.execute(
            "SELECT screenshot_url FROM game_screenshot WHERE app_id = %s",
            (app_id,),
        )
        game["screenshots"] = [row["screenshot_url"] for row in cur.fetchall()]

        cur.execute(
            """
            SELECT l.name AS language, gl.support_type
            FROM game_language gl
            JOIN language l ON gl.language_id = l.language_id
            WHERE gl.app_id = %s
            """,
            (app_id,),
        )
        game["languages"] = cur.fetchall()

    return game
