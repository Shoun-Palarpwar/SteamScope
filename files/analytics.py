"""
STEAMSCOPE API - ANALYTICS ENDPOINTS

GET /analytics/top-games         ranked list by a chosen metric
GET /analytics/genre-stats       game count / avg price / avg score per genre
GET /analytics/platform-stats    game count per platform
GET /analytics/yearly-releases   number of games released per year
"""

from fastapi import APIRouter, HTTPException, Query

from db import get_cursor


router = APIRouter()

TOP_GAMES_METRICS = {
    "positive_reviews": "g.positive_reviews",
    "recommendation_count": "g.recommendation_count",
    "metacritic_score": "g.metacritic_score",
    "peak_ccu": "g.peak_ccu",
}


@router.get("/top-games")
def top_games(
    by: str = Query("positive_reviews", description=f"One of: {', '.join(TOP_GAMES_METRICS)}"),
    limit: int = Query(10, ge=1, le=100),
):
    if by not in TOP_GAMES_METRICS:
        raise HTTPException(400, f"'by' must be one of: {', '.join(TOP_GAMES_METRICS)}")

    metric_col = TOP_GAMES_METRICS[by]

    query = f"""
        SELECT g.app_id, g.name, g.release_date, {metric_col} AS metric_value,
               g.header_image_url
        FROM game g
        WHERE {metric_col} IS NOT NULL
        ORDER BY {metric_col} DESC
        LIMIT %s
    """

    with get_cursor() as cur:
        cur.execute(query, (limit,))
        rows = cur.fetchall()

    return {"metric": by, "results": rows}


@router.get("/genre-stats")
def genre_stats():
    query = """
        SELECT
            gr.name AS genre,
            COUNT(*) AS game_count,
            ROUND(AVG(g.price), 2) AS avg_price,
            ROUND(AVG(g.metacritic_score), 1) AS avg_metacritic_score,
            ROUND(AVG(g.positive_reviews), 0) AS avg_positive_reviews
        FROM genre gr
        JOIN game_genre gg ON gr.genre_id = gg.genre_id
        JOIN game g ON gg.app_id = g.app_id
        GROUP BY gr.genre_id, gr.name
        ORDER BY game_count DESC
    """
    with get_cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return {"results": rows}


@router.get("/platform-stats")
def platform_stats():
    query = """
        SELECT
            p.name AS platform,
            COUNT(*) AS game_count,
            ROUND(AVG(g.price), 2) AS avg_price
        FROM platform p
        JOIN game_platform gp ON p.platform_id = gp.platform_id
        JOIN game g ON gp.app_id = g.app_id
        GROUP BY p.platform_id, p.name
        ORDER BY game_count DESC
    """
    with get_cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return {"results": rows}


@router.get("/yearly-releases")
def yearly_releases():
    query = """
        SELECT
            YEAR(g.release_date) AS year,
            COUNT(*) AS games_released
        FROM game g
        WHERE g.release_date IS NOT NULL
        GROUP BY YEAR(g.release_date)
        ORDER BY year
    """
    with get_cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return {"results": rows}
