"""Pooled raw SQL access. Each context is a transaction."""
import os
from contextlib import contextmanager
from threading import BoundedSemaphore
from mysql.connector.errors import PoolError
from mysql.connector.pooling import MySQLConnectionPool

_pool = None
_slots = BoundedSemaphore(5)

def start_pool():
    global _pool
    config = dict(host=os.getenv("DB_HOST", "127.0.0.1"),
                  port=int(os.getenv("DB_PORT", "3306")),
                  user=os.getenv("DB_USER", "root"),
                  password=os.getenv("DB_PASSWORD", ""),
                  database=os.getenv("DB_NAME", "steamscope"),
                  connection_timeout=5)
    if os.getenv("DB_SOCKET"):
        config["unix_socket"] = os.environ["DB_SOCKET"]
    _pool = MySQLConnectionPool(pool_name="steamscope", pool_size=5, **config)

@contextmanager
def get_cursor(dictionary=True):
    if _pool is None:
        raise RuntimeError("Database pool has not started")
    if not _slots.acquire(timeout=10):
        raise PoolError('Database is busy; retry shortly')
    conn = None
    cursor = None
    try:
        conn = _pool.get_connection()
        cursor = conn.cursor(dictionary=dictionary, buffered=True)
        yield cursor
        conn.commit()
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            try:
                if conn is not None:
                    conn.close()
            finally:
                _slots.release()
