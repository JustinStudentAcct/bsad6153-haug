# ingest/

Code that moves data from your API into your database. You build it with your AI agent, one piece per week:

| Week | File | What it does |
|---|---|---|
| 1 | `fetch.py` | Calls your API: authentication, pagination, rate limits, retries. Saves raw JSON to `data/raw/`. |
| 2 | `load.py` | Turns the raw JSON into rows in your tables, using parameterized queries. Running it twice must not create duplicates. |
| 3 | `sync.py` | Combines fetch and load into one incremental, idempotent sync that GitHub Actions runs on a schedule and records in `sync_runs`. |

The initial load and scheduled sync connect as the database owner (`DATABASE_URL`).
The website and chatbot use a separate read-only connection.

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

## Load the Milestone 1 snapshot into Supabase

1. In the Supabase dashboard, open **Connect** and choose **Session pooler** on port
   `5432`. Replace `[YOUR-PASSWORD]` with your database password, percent-encoding
   any URI-reserved characters in the password. Save the URI as `DATABASE_URL`
   in your local `.env`. [Supabase connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres#shared-pooler-session-mode)
2. Confirm the connection from the project root.

   ```powershell
   .venv/Scripts/python.exe scripts/check_db.py
   ```

3. In the Supabase SQL Editor, run [db/schema.sql](../db/schema.sql) once to create
   the three recipe tables.
4. Load the combined October 30 file, then rerun the same command to verify it
   inserts zero additional rows. If you collected your own snapshot, substitute
   the path to its combined `recipes.json`.

   ```powershell
   .venv/Scripts/python.exe ingest/load.py data/raw/themealdb_20261030T212358782687Z/recipes.json
   ```

5. Run the statements in [db/queries.sql](../db/queries.sql) individually in the
   SQL Editor to inspect their results.

On a fresh local PostgreSQL 16 database, the October 30 snapshot inserted 790
recipes, 946 ingredients, and 8,152 ingredient slots. The second run inserted
zero rows. The loader uses one transaction and keeps each previously loaded
recipe and its slots as they were first imported.
