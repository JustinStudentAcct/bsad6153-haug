"""Report recipe sync freshness and seven-day totals using APP_DATABASE_URL."""

import os
from datetime import UTC
from pathlib import Path

import psycopg
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
STATUS_QUERY = """
    select
        max(finished_at) as last_success,
        max(finished_at) filter (where records_inserted > 0 or records_updated > 0) as last_change,
        coalesce(sum(records_inserted) filter (where finished_at >= now() - interval '7 days'), 0),
        coalesce(sum(records_updated) filter (where finished_at >= now() - interval '7 days'), 0)
    from public.sync_runs
    where status = 'success'
"""


def main():
    load_dotenv(ROOT / ".env")
    url = os.getenv("APP_DATABASE_URL")
    if not url:
        print("APP_DATABASE_URL is not set. Add the app_reader connection string to .env.")
        return 1

    try:
        with psycopg.connect(url, connect_timeout=10) as conn:
            last_success, last_change, inserted, updated = conn.execute(STATUS_QUERY).fetchone()
    except psycopg.Error as error:
        print(f"Could not read sync history ({type(error).__name__}). Check the connection and sync_runs grant.")
        return 1

    success_time = last_success.astimezone(UTC).isoformat(timespec="seconds") if last_success else "None recorded"
    change_time = last_change.astimezone(UTC).isoformat(timespec="seconds") if last_change else "None recorded"
    print(f"Last successful sync (UTC): {success_time}")
    print(f"Last recorded recipe change (UTC): {change_time}")
    print(f"Last 7 days: {inserted} recipes inserted, {updated} recipes updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
