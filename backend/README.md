# SteamScope backend

FastAPI + MySQL, using parameterized raw SQL. The real Steam catalog is paired
with simulated, editable demo profiles. This version has no authentication;
start it on loopback for local development.

## Start on this machine

```sh
cd /Users/shounpalarpwar/Downloads/SteamScope/SteamScope-main/backend
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs. Expand an endpoint, click **Try it out**, fill in
parameters, then **Execute**. The response body is the actual backend result.
Collection edits persist in MySQL and are visible on subsequent GET requests.

## Fresh environment

Python 3.10+ and a running MySQL instance with the populated SteamScope schema
are required. From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` for your database, then launch with:

```sh
python3 -m uvicorn app.main:app --env-file .env --reload --host 127.0.0.1 --port 8000
```

Without `--env-file`, settings come from shell environment variables with the
local defaults in `.env.example`. `DB_SOCKET` optionally selects a Unix socket.
The database must be running before API startup.

For a database that does not yet have `library.is_favorite`, apply
`../database/migrations/001_library_favorites.sql` once using MySQL Workbench
with `steamscope` selected. **This migration has already been applied to the
local database during development. Do not apply it again.** The backend does
not silently migrate or reseed data at startup.

## See the features in interactive docs

1. `GET /health/ready`: confirm database/schema readiness.
2. `GET /users`: select a `user_id` (for example 1).
3. `GET /games`: browse or search; copy an `app_id`.
4. `GET /games/{app_id}`: see the game's attributes and screenshots.
5. `GET /users/{user_id}/library` and `/wishlist`: inspect current membership.
6. For an unowned game, `PUT /users/{user_id}/wishlist/{app_id}` adds it.
7. `PUT /users/{user_id}/library/{app_id}` marks it owned and removes its wishlist entry.
8. `PATCH /users/{user_id}/library/{app_id}/favorite` with
   `{"is_favorite": true}` favorites it. GET `/favorites` to verify persistence.
9. `GET /users/{user_id}/recommendations`: see unowned games and the matching
   attributes/source games that explain each result.
10. `GET /games/{app_id}/similar`: discovery from one game.
11. `GET /analytics/rankings`: use `source=steam&metric=peak_ccu`, or
    `source=community&metric=active_players` (also `owners` and `play_minutes`).

PUT/DELETE success uses HTTP 204 with no response body. An owned game cannot be
wishlisted (409). An unowned game cannot be favorited (404). Repeated adds,
removes, and explicit favorite updates are safe. Removing ownership preserves
historical activity, achievements, and purchases. None of these actions creates
a purchase or a play session.

These are real edits to the chosen **simulated** profile. For exploration
without manual edits, use GET routes. The integration test below uses its own
throwaway profile and cleans up after itself.

## API conventions

- All GET endpoints have declared response schemas in `/docs` and
  `/openapi.json`. Game lists share `GameCard`; collection entries add
  `added_at`, recommendations add scores/reasons, and rankings add metric values.
  Prices are JSON numbers (or null); membership flags are JSON booleans (or null).
- Lists return `total`, `limit`, `offset`, and `results` where paginated.
- `/filters/{kind}` supplies searchable, paginated filter choices: `tag`,
  `genre`, `developer`, `publisher`, `category`, `platform`, `language`.
- `/games` accepts exact-name relationship filters, price ranges, text search,
  and whitelisted sort fields. Price is the catalog's recorded price.
- Similarity sums shared tag (3), genre (1), and developer (2) signals.
  Each favorite seed contributes three times the weight of an ordinary owned
  game. Positive review counts break score ties. A maximum of three pieces of
  evidence per attribute type are returned; all matching attributes contribute
  to the score. Empty/no-match profiles use a labeled popularity fallback.
- Community activity counts PLAY and SESSION records; LAUNCH does not contribute.
  `active_players` counts distinct profiles; `play_minutes` sums recorded duration.
  Dates are inclusive in stored database time. Omitted bounds are unbounded.
  The response includes the available activity range. Metrics are simulated,
  and Steam metrics are stored snapshots; neither is a live player count.
- Existing genre/platform/yearly analytics remain available; expanded analysis
  questions and frontend visual design are still to be decided.

## Frontend integration helpers (0.3.0)

Pass the selected profile as `user_id` to catalog, game detail, similar games,
rankings, and top-games requests. Cards return `is_owned`, `is_wishlisted`,
and `is_favorite`. Without a selected profile these values are null; with a
valid profile they are true/false. A nonexistent profile returns 404, including
when the requested game list is empty. Personal collections and recommendations
use the profile ID in their path automatically.

Cards consistently include `app_id`, `name`, `header_image_url`, `release_date`,
`price`, `genres`, review counts, `metacritic_score`, `recommendation_count`, and
`peak_ccu`. Extra fields are loaded for the current page in batches. Similar-game
membership flags do not change the similarity ranking or hide owned games.

Library, wishlist, and favorites accept `search`, `sort_by=added_at|name`,
`order=asc|desc`, `limit`, and `offset`. Defaults remain recently added first;
favorites sort by the date of library addition, not the date favorited.
`total` reflects the search filter, and equal sort values use ascending app ID.

`GET /users/{user_id}/summary` returns public profile fields, `library_count`,
`wishlist_count`, `favorite_count`, and `data_source: "simulated"`.

Examples to open while the server runs:

- http://127.0.0.1:8000/games?user_id=1&limit=5
- http://127.0.0.1:8000/users/1/library?sort_by=name&order=asc&limit=10
- http://127.0.0.1:8000/users/1/summary

After a successful collection mutation, refresh the affected cards, summary,
and collection lists; favorite/library changes also affect recommendations.
Key frontend caches by profile ID and clear profile-specific state on switching
profiles. PUT/DELETE still return 204, so do not attempt to parse a JSON body.

## Verify

From this directory, with database configuration exported in your environment:

```sh
python3 -m unittest discover -s tests -v
```

The six live integration tests cover the user journey, membership across screens
and profile switches, collection sorting/filtering/pagination, summary counts,
response schemas, recommendation scores checked against attribute intersections,
favorite weighting, inclusive activity date boundaries, distinct-player counts,
missing resources, and transaction rollback. They create and remove isolated
profiles and activity fixtures; auto-increment identifiers may advance. Do not
target a database where temporary test writes are unwanted.

The frontend has not been built yet. `/docs` is the working interface for
exploring and verifying this backend.
