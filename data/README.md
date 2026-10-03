# Datasets

All local project data now lives inside this repository folder.

| Location | Contents |
| --- | --- |
| `raw/games.json` | Authoritative import source; 141,900 source records |
| `raw/games.csv` | Original problematic CSV, retained for the cleaning story; do not import it |
| `cleaned/games_cleaned.csv` | 141,899 retained game records |
| `cleaned/master/` | Seven reusable reference-name files |
| `cleaned/relationships/` | Eight relationship/media files |
| `sample/` | Small Excel samples suitable for GitHub and course review |
| `manifest.json` | Sizes and SHA-256 hashes of the 20 retained dataset files |

Raw and cleaned datasets are currently excluded from ordinary Git commits.
Moving them inside the repository does not itself upload them to GitHub.
They require a separate large-file storage decision; Git LFS is not installed
on the current machine. Samples, this README, and the manifest are tracked
normally. Exact original download attribution remains to be documented.

Duplicate copies from the outer folder were removed only after matching
SHA-256 hashes. The raw archive was also checked against the retained files.
The non-identical initial project ZIP is preserved locally under `extra files/archives/`
and is ignored by Git.

To verify the local data without changing it, run from the repository root:

```sh
python3 - <<'PY'
import hashlib, json
from pathlib import Path
for item in json.loads(Path('data/manifest.json').read_text())['files']:
    path = Path(item['path'])
    assert path.stat().st_size == item['bytes'], path
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    assert digest.hexdigest() == item['sha256'], path
print('All retained dataset files match the manifest.')
PY
```
