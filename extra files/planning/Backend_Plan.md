# SteamScope backend implementation plan

Archived under extra files at the user's request; retained for review.

> Historical planning record. Paths and scope below describe the original workspace.
> See the root README and database/README.md for the current structure and setup.

## Implementation status (2026-10-01)

The backend is now in `backend/`; see `backend/README.md` for setup and the
interactive walkthrough. Catalog reads, collection mutations, favorites,
filter lookups, explainable recommendations, and both ranking sources are
implemented. Migration 001 has been applied locally. The live MySQL journey
integration test passed, including rollback and temporary-profile cleanup.
The original file audit below records the starting state. Frontend design,
expanded analytics, production authentication, and broader performance testing
remain future work.

## Agreed product scope

Frontend integration pass completed on 2026-10-02: shared game-card response
models, profile-aware membership flags, collection search/sorting, and profile
summary counts are implemented. All GET routes declare response schemas.
Six live MySQL integration tests passed, including score correctness and
date-filtered ranking checks. No additional schema migration was needed.

FastAPI, MySQL, and parameterized raw SQL. A searchable demo-profile picker
provides identity for this phase. Real authentication is deferred. The catalog
comes from real Steam data; profile ownership, activity, purchases, and
achievements are simulated. Keep that distinction in API metadata and the UI.

Deliver browsing and game details, editable libraries and wishlists, favorites
within owned games, explainable recommendations, similar games, and separate
catalog-popularity and simulated-community rankings. Existing analytics are a
baseline; the final analysis questions remain open for discussion.

## File audit (2026-10-01)

- The Git repository is `SteamScope-main/`. The supplied API modules are in the
  sibling `files/` directory, outside that repository.
- `files/main.py` imports `routers`, but no such package is present in the
  supplied backend. Router modules use top-level `db` imports.
- Catalog listing supports search, genre, tag, category, platform, price,
  sorting, and pagination. Game detail includes relationships and screenshots.
- User routes read profiles, libraries, wishlists, achievements, and activity.
  There are no collection mutations or profile-list endpoint.
- Analytics include top games, genre/platform summaries, and yearly releases.
- The database pool is created at import time with hardcoded connection settings.
  The cursor helper does not commit or roll back writes.
- `fike1.sql` defines the relational schema; separate schema-repair scripts exist.
  `library` in the supplied schema has no favorite flag. Actual database schema,
  counts, integrity, and query performance have not been verified in this audit.
- Python has FastAPI, Uvicorn, and MySQL Connector available. No runtime API or
  live database test has been performed yet.

## Build order and acceptance criteria

### 1. Runnable foundation

Create `backend/app/` inside the Git repository, with package imports, routers,
request/response models, and shared database access. Port the existing reads.
Use environment-based database settings and explicit local frontend origins.
Manage the connection pool through application lifespan and provide transaction
commit/rollback handling. Separate service health from database readiness.

Verify the actual MySQL schema read-only before applying versioned migrations.
Do not rerun import, schema-creation, or simulation scripts against populated data.
Keep SQL visible and straightforward; introduce a shared recommendation service
where logic is genuinely reused.

Acceptance: documented launch command, successful startup, interactive API docs,
database readiness, and a real catalog request.

### 2. Complete personal collection flow

- `GET /users`: bounded, searchable profile picker; safe public fields only.
- `GET /users/{user_id}` and existing collection reads.
- `PUT` / `DELETE /users/{user_id}/library/{app_id}`.
- `PUT` / `DELETE /users/{user_id}/wishlist/{app_id}`.
- `PATCH /users/{user_id}/library/{app_id}/favorite` with an explicit
  `{"is_favorite": true|false}` body, rather than a retry-sensitive toggle.
- `GET /users/{user_id}/favorites`.

Add a versioned migration for `library.is_favorite` after checking live schema.
Use consistent pagination, deterministic sort tie-breakers, validated IDs and
request bodies, and explicit missing-resource responses.

Implementation defaults: repeated adds/removes are safe; adding an owned game
removes its wishlist entry in the same transaction; wishlisting an owned game
returns a conflict. Favorites require library membership. Removing ownership
removes the favorite with it, while historical purchases, achievements, and
activity remain. Collection editing does not manufacture purchase/play events.

Acceptance: pick a profile, wishlist a game, add it to the library, favorite it,
reload and verify persistence, then remove it. Check duplicate requests,
nonexistent resources, and rollback on failed writes.

### 3. Discovery and recommendations

Add lookup endpoints for filter options and fill catalog filtering gaps needed
by the frontend, including developer/publisher/language where useful. Validate
price ranges and use stable pagination ordering.

- `GET /games/{app_id}/similar`.
- `GET /users/{user_id}/recommendations`.

Build shared scoring primitives for tags, genres, and developer overlap. Tags
represent style only to the extent the data supports it. Weight favorites more
than ordinary ownership; use popularity as a secondary signal. Exclude owned
games from personal results and the source game from similar results. Return
concrete matching attributes and source-game evidence for explanations. Use a
labeled popularity fallback for profiles without usable preference signals.

Aggregate each relationship independently to prevent many-to-many join score
inflation. Measure query plans and timings on the real catalog before deciding
on extra indexes, candidate limits, or caching.

Acceptance: relevant matches with truthful explanations, no forbidden results,
empty-profile behavior, and measured latency on representative profiles.

### 4. Rankings and analytics baseline

`GET /analytics/rankings?source=steam|community&metric=...` validates metrics
against the selected source and returns source labels and metric definitions.

Steam metrics: recorded peak concurrent players, positive review counts, and
recommendation counts. These are catalog snapshots, not live measurements.

Community metrics: ownership counts, distinct active demo profiles, and recorded
play minutes. Define which event types qualify after inspecting the generator
and data. Support explicit date windows for activity and expose the dataset's
activity range so older simulated data does not appear to be current.

Preserve current analytics routes; review missing-value and zero-score semantics
before presenting averages. Discuss additional analysis questions separately.

Acceptance: independently checked aggregates, stable ordering, truthful source
labels, and clearly defined date boundaries and metrics.

### 5. Frontend handoff

Provide setup/environment documentation, endpoint examples, response contracts,
and a reproducible smoke-test flow. Start frontend integration after stage 2;
discovery and rankings can follow against the same contracts. Validate SQL and
transactions against MySQL; mocked tests alone cannot establish correctness.

The first frontend flow is profile selection -> catalog -> game detail ->
wishlist/library -> favorite -> recommendations. Visual design remains a
separate discussion.
