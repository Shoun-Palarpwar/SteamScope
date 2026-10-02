"""Live MySQL test; creates and removes an isolated profile."""
import time
import unittest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_cursor

class Integration(unittest.TestCase):
    def test_journey(self):
        with TestClient(app) as c:
            for url in ['/health/ready','/openapi.json','/games','/filters/tag']:
                r=c.get(url); self.assertEqual(r.status_code,200,r.text)
            game=c.get('/games',params={'limit':1}).json()['results'][0]['app_id']
            self.assertEqual(c.get(f'/games/{game}').status_code,200)
            self.assertEqual(c.get('/games',params={'min_price':10,'max_price':1}).status_code,422)
            self.assertEqual(c.get('/games',params={'order':'ASC'}).status_code,200)
            name='test_'+uuid.uuid4().hex[:20]
            with get_cursor() as cur:
                cur.execute('INSERT INTO `user` (username,email,password_hash) VALUES (%s,%s,%s)',(name,name+'@example.invalid','test'))
                uid=cur.lastrowid
            base=f'/users/{uid}'
            try:
                self.assertEqual(c.get('/users',params={'search':name}).json()['total'],1)
                self.assertEqual(c.get(base+'/recommendations').json()['strategy'],'popular_fallback')
                for _ in range(2): self.assertEqual(c.put(base+f'/wishlist/{game}').status_code,204)
                self.assertEqual(c.get(base+'/wishlist').json()['total'],1)
                for _ in range(2): self.assertEqual(c.put(base+f'/library/{game}').status_code,204)
                self.assertEqual(c.get(base+'/wishlist').json()['total'],0)
                self.assertEqual(c.get(base+'/library').json()['total'],1)
                self.assertEqual(c.put(base+f'/wishlist/{game}').status_code,409)
                for _ in range(2): self.assertEqual(c.patch(base+f'/library/{game}/favorite',json={'is_favorite':True}).status_code,200)
                self.assertEqual(c.get(base+'/favorites').json()['total'],1)
                self.assertEqual(c.patch(base+f'/library/{game}/favorite',json={'is_favorite':'yes'}).status_code,422)
                for url in [base+'/recommendations',f'/games/{game}/similar','/users/1/recommendations']:
                    start=time.perf_counter(); r=c.get(url,params={'limit':5}); print(url,round(time.perf_counter()-start,3),'seconds')
                    self.assertEqual(r.status_code,200,r.text)
                    rows=r.json()['results']; self.assertTrue(rows); self.assertTrue(rows[0]['reasons'])
                    if url!='/users/1/recommendations': self.assertNotIn(game,[x['app_id'] for x in rows])
                for source,metric in [('steam','peak_ccu'),('community','owners'),('community','active_players'),('community','play_minutes')]:
                    start=time.perf_counter(); r=c.get('/analytics/rankings',params={'source':source,'metric':metric,'limit':3}); print(metric,round(time.perf_counter()-start,3),'seconds')
                    self.assertEqual(r.status_code,200,r.text); self.assertTrue(r.json()['results'])
                self.assertEqual(c.get('/analytics/rankings',params={'source':'community','metric':'peak_ccu'}).status_code,422)
                self.assertEqual(c.get('/analytics/rankings',params={'start_date':'2026-01-01'}).status_code,422)
                for route in ['genre-stats','platform-stats','yearly-releases','top-games']:
                    r=c.get('/analytics/'+route); self.assertEqual(r.status_code,200,r.text)
                for _ in range(2): self.assertEqual(c.delete(base+f'/library/{game}').status_code,204)
                self.assertEqual(c.get(base+'/favorites').json()['total'],0)
                self.assertEqual(c.patch(base+f'/library/{game}/favorite',json={'is_favorite':True}).status_code,404)
                with self.assertRaises(RuntimeError):
                    with get_cursor() as cur:
                        cur.execute('INSERT INTO wishlist (user_id,app_id) VALUES (%s,%s)',(uid,game))
                        raise RuntimeError('force rollback')
                self.assertEqual(c.get(base+'/wishlist').json()['total'],0)
            finally:
                with get_cursor() as cur: cur.execute('DELETE FROM `user` WHERE user_id=%s',(uid,))
            self.assertEqual(c.get(base).status_code,404)
