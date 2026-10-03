"""
STEAMSCOPE API - DATABASE CONNECTION POOL

Shared MySQL connection pool, raw SQL (no ORM), matching the style
of scripts/load_games.py and the other ETL loaders.
"""

from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "steamscope",
}

_pool = pooling.MySQLConnectionPool(
    pool_name="steamscope_pool",
    pool_size=5,
    **DB_CONFIG,
)


@contextmanager
def get_cursor(dictionary=True):
    """
    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM game WHERE app_id = %s", (app_id,))
            row = cur.fetchone()
    Yields a cursor with results as dicts (column_name -> value) by
    default, since that's what FastAPI can return directly as JSON.
    """
    conn = _pool.get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor
    finally:
        cursor.close()
        conn.close()
