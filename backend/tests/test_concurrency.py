from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import unittest

from fastapi.testclient import TestClient
from app.main import app
from app.db import get_cursor


class ConcurrentReads(unittest.TestCase):
    def test_dashboard_burst_waits_for_connections(self):
        barrier = Barrier(10)

        def read(_):
            barrier.wait(timeout=5)
            with get_cursor() as cur:
                cur.execute('SELECT SLEEP(0.05) AS result')
                return cur.fetchone()['result']

        with TestClient(app), ThreadPoolExecutor(max_workers=10) as executor:
            self.assertEqual(list(executor.map(read, range(10))), [0] * 10)
