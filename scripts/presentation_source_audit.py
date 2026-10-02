"""Profile the original JSON without modifying it or rerunning the import."""
import json
from pathlib import Path
import ijson

root = Path(__file__).resolve().parents[1]
source = root.parent / 'games.json'
counts = dict(records=0, invalid_ids=0, missing_names=0, duplicate_ids=0, retained=0)
seen = set()
samples = []
with source.open('rb') as handle:
    for identifier, game in ijson.kvitems(handle, ''):
        counts['records'] += 1
        name = game.get('name')
        if name is None or isinstance(name, str) and not name.strip():
            counts['missing_names'] += 1
            continue
        try:
            app_id = int(identifier)
        except (ValueError, TypeError):
            counts['invalid_ids'] += 1
            continue
        if app_id in seen:
            counts['duplicate_ids'] += 1
            continue
        seen.add(app_id)
        counts['retained'] += 1
        if app_id in (10, 730):
            samples.append(dict(app_id=app_id, name=name, genres=game.get('genres'),
                developers=game.get('developers'), release_date=game.get('release_date'),
                tags=list((game.get('tags') or {}).keys())[:5]))
result = dict(source='games.json', bytes=source.stat().st_size, counts=counts, samples=samples)
out = root / 'frontend/src/presentation/source-audit.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, default=str) + '\n')
print(json.dumps(result, indent=2, default=str))
