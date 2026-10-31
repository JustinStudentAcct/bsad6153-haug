# ingest/

Code that moves data from your API into your database. You build it with your AI agent, one piece per week:

| Week | File | What it does |
|---|---|---|
| 1 | `fetch.py` | Calls your API: authentication, pagination, rate limits, retries. Saves raw JSON to `data/raw/`. |
| 2 | `load.py` | Turns the raw JSON into rows in your tables, using parameterized queries. Running it twice must not create duplicates. |
| 3 | `sync.py` | Combines fetch and load into one incremental, idempotent sync that GitHub Actions runs on a schedule and records in `sync_runs`. |

Only the sync connects as the database owner (`DATABASE_URL`). Everything else uses a limited role.

## Fetch recipes from a clean start

From the project root in PowerShell, run:

```powershell
.venv/Scripts/python.exe ingest/fetch.py
```

No previous downloads are needed. The script uses TheMealDB's public educational key `1`;
it does not read `.env` or connect to the database. Each run creates a new timestamped
`data/raw/themealdb_<UTC timestamp>/` folder containing:

- `response_a_1.json` through `response_z_1.json`: original response bytes, with additional
  numbered files if retries are needed. Non-200 response bodies use `.body`.
- `recipes.json`: all valid recipes combined and deduplicated by `idMeal`.
- `summary.json`: counts by letter, failures, skipped records, and completion status.
- `run.log`: progress and retry messages.

The script requests every letter from `a` through `z`, even if a letter has no recipes.
This is alphabetical traversal, not numbered pagination. It waits at least one second
between requests and retries transient failures up to three total attempts per letter.
For HTTP 429 it honors `Retry-After` when supplied, with exponential backoff otherwise.
Failed letters are logged and the script continues; interrupted runs preserve partial results.
A successful exit requires all 26 letters and at least 500 unique valid recipes.

The previous exploratory probe and extension scripts have been replaced by `fetch.py`.
Existing downloads remain untouched. This script fetches recipes only; retrieving a second
resource type is still outstanding for the assignment.
