# Database setup

`schema.sql` is the current 24-table schema, reconstructed from the saved
`SHOW CREATE TABLE` evidence captured on 2026-10-02. It includes all 27 foreign
keys and `library.is_favorite`. Auto-increment counters from the populated
database were removed. Tables appear in dependency order; foreign-key checks
remain enabled. This is a schema, not a backup of the database's rows.

## Existing development database

Keep using it. Folder cleanup does not require reimporting anything.
`checks/schema_audit.sql` and `checks/data_integrity.sql` are read-only checks.
The latter covers the historical diagnostic queries; the presentation snapshot
script audits every declared foreign key.

## Fresh, empty database only

Install MySQL 8 and run from the repository root:

```sh
mysql -u root -p < database/schema.sql
python3 -m pip install -r scripts/requirements.txt
```

The schema targets `steamscope`; change its CREATE DATABASE and USE statements
if you choose a different name. It deliberately does not drop existing tables.
Do not run it over your current populated database.

Set `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` in your shell
as needed. Data scripts use the same defaults as `backend/.env.example`.
They do not automatically read `.env`. A shell-compatible environment file can
be loaded with `set -a; source backend/.env; set +a` before running the scripts.

Place the original JSON at `data/raw/games.json`, then run in this order:

```sh
python3 scripts/clean_games_json.py
python3 scripts/extract_relationships_json.py
python3 scripts/load_games.py
python3 scripts/load_relationships.py
python3 scripts/generate_simulated_data.py
mysql -u root -p < database/checks/data_integrity.sql
```

The first two steps regenerate CSV files; the next three write to MySQL.
If the cleaned files already match `data/manifest.json`, the first two steps
can be skipped. Imports are not a migration or repair system: populated tables
are skipped or rejected, so a partially completed import needs investigation.
The generator creates simulated profiles and activity; it does not load real
Steam users. Exact generated dates can vary between runs.

This reorganized pipeline has been checked for paths, imports, and schema
consistency, but a full import into a fresh MySQL database has not been rerun.
The current development database was not modified during cleanup.

## Migrations and history

`migrations/001_library_favorites.sql` is only for an older database missing
`library.is_favorite`. Do not apply it after the current `schema.sql` or to the
existing development database where that column is already present.

`extra files/sql/` preserves the original schema and one-time repair for explaining
the project's evolution. Those files are not setup instructions.
