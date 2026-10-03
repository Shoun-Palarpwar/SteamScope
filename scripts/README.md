# Project tools

Run commands from the repository root. Dataset paths are anchored to the
repository, so moving the outer SteamScope folder does not change them.
Install dependencies with `python3 -m pip install -r scripts/requirements.txt`.

| Tool | Purpose | Effects |
| --- | --- | --- |
| `clean_games_json.py` | Stream the original JSON and clean game records | Rewrites cleaned game CSV |
| `extract_relationships_json.py` | Extract reference names and game relationships | Rewrites master and relationship CSVs |
| `load_games.py` | Import cleaned catalog into an empty game table | Writes MySQL |
| `load_relationships.py` | Import references and relationships | Writes MySQL |
| `generate_simulated_data.py` | Create demonstration users and activity | Writes MySQL |
| `project_config.py` | Shared environment-based connection settings | No connection on import |
| `profile_raw_data.py` | Inspect historical CSV quality | Reads raw files |
| `presentation_source_audit.py` | Count records and capture source examples | Writes saved source evidence |
| `presentation_snapshot.py` | Audit tables, columns, foreign keys and counts | Reads MySQL; writes saved evidence |
| `presentation_diagrams.py` | Build schema maps from saved evidence | Writes diagram JSON |
| `build_presentation_pdf.py` | Build the printable presentation | Writes PDF and frontend download copy |

See `database/README.md` for import order and connection configuration.
Presentation JSON is under `frontend/src/presentation/`; it is committed so the
interactive presentation can work without a database connection. The PDF
generator remains work in progress and its layout needs final review.

Earlier CSV repair, review-dataset experiments, debugging scripts, and the
unused backend skeleton are preserved under `extra files/`. See its README
for recovery notes. Only the maintained tools are kept in this folder.
