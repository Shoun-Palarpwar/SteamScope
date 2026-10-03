# Earlier work — kept for review

This folder preserves earlier project work separately from the active app.
Do not use these scripts or SQL as current setup instructions. Some contain
old paths, superseded schemas, or assumptions about datasets no longer used.

| Folder | What it preserves |
| --- | --- |
| `legacy_scripts/` | 25 earlier cleaning, profiling, validation and review experiments restored from Git HEAD |
| `backend_prototype/` | Seven files from the original, unused backend skeleton |
| `sql/` | Original schema, historical repair, and recovered scratch-query text |
| `planning/` | The earlier backend implementation plan |
| `archives/` | Original project ZIP, kept locally and ignored by Git |

Hard-coded database passwords in restored scripts were replaced with empty
strings before making the archive Git-ready. This does not remove credentials
from older Git commits. The original ZIP is kept out of Git because it can
contain the same historical credentials.

## Recovery notes

The instruction to archive instead of delete arrived after some cleanup had
already happened. All 32 removed tracked code files were restored here from
Git; they were unchanged in the working tree before cleanup.

The loose `fike2.sql`, `fike3.sql`, and `fike4.sql` files had already been
deleted and were not tracked. The captured inspection queries from `fike2.sql`
are retained as `fike2.recovered.sql`; captured text from `fike4.sql` is retained
as `fike4.recovered-excerpt.txt`. The complete original `fike3.sql` could not be
recovered. Its intended role was intermediate table creation; the original
design in `sql/fike1.sql` and current `database/schema.sql` remain available.

Older loose copies of `load_relationships.py` and `generate_simulated_data.py`
had also been removed in favor of the newer repository versions. Their exact
loose-file versions were not recovered. The maintained versions remain under
`scripts/`, with pre-cleanup repository versions available in Git history.

Duplicate datasets were removed only after matching hashes. One complete copy
of every distinct dataset remains under `data/`; `data/manifest.json` records
their checksums. The duplicate raw ZIP was checked against the retained source
files before removal. No current MySQL data was changed.
