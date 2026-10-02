"""Live checks on isolated profiles; existing catalog and profiles are untouched."""
import unittest
import uuid

from fastapi.testclient import TestClient

from app.db import get_cursor
from app.main import app
from app.schemas import GameCard


class FrontendContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app).__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def setUp(self):
        self.user_ids = []
        self.addCleanup(self.cleanup_profiles)
        with get_cursor() as cur:
            cur.execute('SELECT app_id, name FROM game ORDER BY positive_reviews DESC, app_id LIMIT 3')
            self.games = cur.fetchall()
            for _ in range(2):
                name = 'ux_test_' + uuid.uuid4().hex[:20]
                cur.execute('INSERT INTO `user` (username,email,password_hash) VALUES (%s,%s,%s)',
                            (name, name + '@example.invalid', 'test'))
                self.user_ids.append(cur.lastrowid)
        self.uid, self.other_uid = self.user_ids
        self.base = f'/users/{self.uid}'

    def cleanup_profiles(self):
        with get_cursor() as cur:
            for uid in self.user_ids:
                cur.execute('DELETE FROM `user` WHERE user_id=%s', (uid,))

    def get(self, url, **params):
        response = self.client.get(url, params=params)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def add(self, collection, game):
        response = self.client.put(f'{self.base}/{collection}/{game}')
        self.assertEqual(response.status_code, 204, response.text)

    def test_membership_summary_and_card_consistency(self):
        game = self.games[0]['app_id']
        detail_url = f'/games/{game}'
        anonymous = self.get(detail_url)
        self.assertIsNone(anonymous['is_owned'])
        empty = self.get(self.base + '/summary')
        self.assertEqual([empty[k] for k in ['library_count', 'wishlist_count', 'favorite_count']], [0, 0, 0])
        self.add('wishlist', game)
        wished = self.get(detail_url, user_id=self.uid)
        self.assertIs(wished['is_wishlisted'], True)
        self.assertIs(wished['is_owned'], False)
        wishlist_card = self.get(self.base + '/wishlist')['results'][0]
        for key in GameCard.model_fields:
            self.assertEqual(wishlist_card[key], wished[key], key)
        self.assertEqual(self.get(self.base + '/summary')['wishlist_count'], 1)
        self.add('library', game)
        response = self.client.patch(f'{self.base}/library/{game}/favorite', json={'is_favorite': True})
        self.assertEqual(response.status_code, 200)
        owned = self.get(detail_url, user_id=self.uid)
        self.assertIs(owned['is_owned'], True)
        self.assertIs(owned['is_favorite'], True)
        self.assertIs(owned['is_wishlisted'], False)
        summary = self.get(self.base + '/summary')
        self.assertEqual([summary[k] for k in ['library_count', 'wishlist_count', 'favorite_count']], [1, 0, 1])
        for route, params in [('/games', {'search': self.games[0]['name'], 'user_id': self.uid}),
                              (self.base + '/library', {}), (self.base + '/favorites', {})]:
            card = next(r for r in self.get(route, **params)['results'] if r['app_id'] == game)
            for key in GameCard.model_fields:
                self.assertEqual(card[key], owned[key], key)
        # Switching profiles must not reuse membership from the previous viewer.
        other = self.get(detail_url, user_id=self.other_uid)
        self.assertIs(other['is_owned'], False)
        self.assertIs(other['is_favorite'], False)
        similar = self.get(f'/games/{game}/similar', user_id=self.uid, limit=3)
        for card in similar['results']:
            self.assertTrue(set(GameCard.model_fields).issubset(card))
            self.assertIs(card['is_owned'], False)
        self.assertEqual(self.client.delete(f'{self.base}/library/{game}').status_code, 204)
        self.assertEqual(self.get(self.base + '/summary')['favorite_count'], 0)

    def test_collection_search_sort_and_pagination(self):
        with get_cursor() as cur:
            for index, game in enumerate(self.games):
                # Same timestamp tests the app_id tie-breaker across pages.
                cur.execute('INSERT INTO `library` (user_id,app_id,added_at,is_favorite) VALUES (%s,%s,%s,TRUE)',
                            (self.uid, game['app_id'], '2026-01-01 12:00:00'))
                cur.execute('INSERT INTO wishlist (user_id,app_id) VALUES (%s,%s)', (self.other_uid, game['app_id']))
        for route in [self.base + '/library', self.base + '/favorites', f'/users/{self.other_uid}/wishlist']:
            asc = self.get(route, sort_by='name', order='asc')['results']
            desc = self.get(route, sort_by='name', order='desc')['results']
            self.assertEqual([r['name'] for r in asc], sorted(r['name'] for r in asc))
            self.assertEqual([r['name'] for r in desc], list(reversed([r['name'] for r in asc])))
            filtered = self.get(route, search=self.games[0]['name'], limit=1)
            self.assertEqual(filtered['total'], 1)
            self.assertEqual(filtered['results'][0]['app_id'], self.games[0]['app_id'])
            self.assertEqual(self.get(route, search='no_such_title_' + uuid.uuid4().hex)['total'], 0)
            self.assertEqual(self.get(route, offset=99)['results'], [])
            self.assertEqual(self.client.get(route, params={'sort_by': 'invalid'}).status_code, 422)
        pages = [self.get(self.base + '/library', limit=1, offset=i)['results'][0]['app_id'] for i in range(3)]
        self.assertEqual(pages, sorted(g['app_id'] for g in self.games))

    def test_recommendation_scores_against_set_intersections(self):
        seed = self.games[0]['app_id']
        self.add('library', seed)
        before = self.get(self.base + '/recommendations', limit=3)
        self.assertEqual(before['strategy'], 'attribute_overlap')
        seed_detail = self.get(f'/games/{seed}')
        for card in before['results']:
            candidate = self.get(f"/games/{card['app_id']}")
            expected = sum(weight * len(set(seed_detail[kind]) & set(candidate[kind]))
                           for kind, weight in [('tags', 3), ('genres', 1), ('developers', 2)])
            self.assertEqual(card['match_score'], expected)
            self.assertNotEqual(card['app_id'], seed)
            self.assertIs(card['is_owned'], False)
            for reason in card['reasons']:
                key = {'tag': 'tags', 'genre': 'genres', 'developer': 'developers'}[reason['type']]
                self.assertIn(reason['attribute'], set(seed_detail[key]) & set(candidate[key]))
                self.assertEqual(reason['source_app_id'], seed)
        self.client.patch(f'{self.base}/library/{seed}/favorite', json={'is_favorite': True})
        after = self.get(self.base + '/recommendations', limit=3)
        self.assertEqual([r['app_id'] for r in before['results']], [r['app_id'] for r in after['results']])
        self.assertEqual([r['match_score'] * 3 for r in before['results']], [r['match_score'] for r in after['results']])

    def test_ranking_date_boundaries_and_distinct_players(self):
        game = self.games[0]['app_id']
        params = dict(source='community', metric='play_minutes', start_date='1001-01-02', end_date='1001-01-02')
        # Dedicated ancient fixture window; do not assume current seeded activity dates.
        self.assertEqual(self.get('/analytics/rankings', **params)['results'], [])
        events = [(self.uid, 'PLAY', '1001-01-01 23:59:59', 999),
                  (self.uid, 'PLAY', '1001-01-02 00:00:00', 10),
                  (self.uid, 'SESSION', '1001-01-02 12:00:00', 20),
                  (self.other_uid, 'PLAY', '1001-01-02 23:59:59', 30),
                  (self.uid, 'LAUNCH', '1001-01-02 15:00:00', 888),
                  (self.uid, 'PLAY', '1001-01-03 00:00:00', 777)]
        with get_cursor() as cur:
            cur.executemany('INSERT INTO user_activity (user_id,app_id,activity_type,activity_time,duration_minutes) VALUES (%s,%s,%s,%s,%s)',
                            [(uid, game, kind, timestamp, minutes) for uid, kind, timestamp, minutes in events])
        self.assertEqual(self.get('/analytics/rankings', **params)['results'][0]['metric_value'], 60)
        params['metric'] = 'active_players'
        self.assertEqual(self.get('/analytics/rankings', **params)['results'][0]['metric_value'], 2)
        params['end_date'] = '1001-01-01'
        self.assertEqual(self.client.get('/analytics/rankings', params=params).status_code, 422)

    def test_missing_resources_and_openapi_contracts(self):
        # A profile created by this test and then removed is guaranteed absent.
        with get_cursor() as cur:
            cur.execute('DELETE FROM `user` WHERE user_id=%s', (self.other_uid,))
        missing = self.other_uid
        for route in ['/games', f"/games/{self.games[0]['app_id']}",
                      f"/games/{self.games[0]['app_id']}/similar", '/analytics/rankings', '/analytics/top-games']:
            self.assertEqual(self.client.get(route, params={'user_id': missing}).status_code, 404)
        for suffix in ['summary', 'library', 'wishlist', 'favorites', 'recommendations']:
            self.assertEqual(self.client.get(f'/users/{missing}/{suffix}').status_code, 404)
        self.assertEqual(self.client.get('/games/-1').status_code, 404)
        self.assertEqual(self.client.put(f'{self.base}/library/-1').status_code, 404)
        schema = self.get('/openapi.json')
        for path, methods in schema['paths'].items():
            for method, operation in methods.items():
                if method != 'get':
                    continue
                response = operation['responses']['200']['content']['application/json']['schema']
                self.assertIn('$ref', response, path)
