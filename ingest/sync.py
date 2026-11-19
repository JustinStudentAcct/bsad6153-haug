"""Fetch TheMealDB recipes and apply changes in one database transaction."""

import logging
import os
from datetime import UTC, datetime
from typing import NamedTuple
from uuid import UUID, uuid4

import psycopg
from dotenv import load_dotenv

from fetch import fetch_snapshot
from load import ROOT, read_snapshot


LOG = logging.getLogger(__name__)


class Run(NamedTuple):
    run_id: UUID
    started_at: datetime
    trigger: str


def apply_snapshot(conn, recipe_rows, slots_by_meal):
    """Upsert changed recipes and reconcile their slots in the caller's transaction."""
    with conn.cursor() as cursor:
        # Serialize recipe writers while comparing and applying the snapshot.
        cursor.execute("lock table public.recipes in share row exclusive mode")
        cursor.execute(
            "select meal_id from public.recipes where meal_id = any(%s)",
            (list(slots_by_meal),),
        )
        existing_meal_ids = {meal_id for (meal_id,) in cursor}
        cursor.executemany(
            """
            insert into public.recipes as stored (
                meal_id, name, category, country, area, instructions,
                image_url, source_url, source_modified_at, raw_payload
            )
            select %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            where not exists (
                select 1 from public.recipes
                where meal_id = %s and raw_payload = %s
            )
            on conflict (meal_id) do update set
                name = excluded.name,
                category = excluded.category,
                country = excluded.country,
                area = excluded.area,
                instructions = excluded.instructions,
                image_url = excluded.image_url,
                source_url = excluded.source_url,
                source_modified_at = excluded.source_modified_at,
                raw_payload = excluded.raw_payload,
                last_updated_at = statement_timestamp()
            where stored.raw_payload is distinct from excluded.raw_payload
            returning meal_id, recipe_id
            """,
            # Compare the meal ID and raw payload before allocating an identity value.
            ((*row, row[0], row[-1]) for row in recipe_rows),
            returning=True,
        )
        changed_recipes = dict(row for result in cursor.results() for row in result.fetchall())
        if not changed_recipes:
            return 0, 0, 0, 0, 0

        updated_recipes = len(changed_recipes.keys() & existing_meal_ids)
        inserted_recipes = len(changed_recipes) - updated_recipes

        ingredients = {}
        slot_rows = []
        current_slots = []
        for meal_id, recipe_id in changed_recipes.items():
            slots = slots_by_meal[meal_id]
            current_slots.append((recipe_id, [slot for slot, _, _ in slots]))
            for slot, name, measure in slots:
                key = name.casefold()
                ingredients.setdefault(key, name)
                slot_rows.append((recipe_id, slot, key, measure))

        cursor.executemany(
            """
            insert into public.ingredients (ingredient_key, name)
            values (%s, %s)
            on conflict (ingredient_key) do nothing
            """,
            sorted(ingredients.items()),
        )
        added_ingredients = cursor.rowcount
        cursor.executemany(
            """
            insert into public.recipe_ingredients as stored (
                recipe_id, slot_number, ingredient_key, measure
            )
            values (%s, %s, %s, %s)
            on conflict (recipe_id, slot_number) do update set
                ingredient_key = excluded.ingredient_key,
                measure = excluded.measure,
                last_updated_at = statement_timestamp()
            where (stored.ingredient_key, stored.measure)
                is distinct from (excluded.ingredient_key, excluded.measure)
            """,
            slot_rows,
        )
        changed_slots = cursor.rowcount
        cursor.executemany(
            """
            delete from public.recipe_ingredients
            where recipe_id = %s and not (slot_number = any(%s::smallint[]))
            """,
            current_slots,
        )
        return inserted_recipes, updated_recipes, added_ingredients, changed_slots, cursor.rowcount


def record_run(conn, run, status, fetched, *, inserted=0, updated=0, error_message=None):
    conn.execute(
        """
        insert into public.sync_runs (
            run_id, started_at, finished_at, status, records_fetched,
            records_inserted, records_updated, error_message, "trigger"
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (run_id) do nothing
        """,
        (run.run_id, run.started_at, datetime.now(UTC), status, fetched,
         inserted, updated, error_message, run.trigger),
    )


def record_failed_run(url, run, status, fetched, message):
    LOG.error("%s", message)
    try:
        with psycopg.connect(url, connect_timeout=10) as conn:
            record_run(conn, run, status, fetched, error_message=message)
    except psycopg.Error as error:
        LOG.error("Could not write sync history for run %s (%s).", run.run_id, type(error).__name__)
    return 1


def main():
    started_at = datetime.now(UTC)
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        LOG.error("DATABASE_URL is not set. Add the Session pooler URI to .env.")
        return 1

    trigger = "schedule" if os.getenv("GITHUB_EVENT_NAME") == "schedule" else "manual"
    run = Run(uuid4(), started_at, trigger)
    fetched = 0
    failure_message = "Could not fetch or save the TheMealDB snapshot."
    try:
        output, summary = fetch_snapshot()
        fetched = summary["unique_recipe_count"]
        if not summary["complete"] or summary["skipped_records"]:
            LOG.error("Snapshot rejected. See %s for fetch details.", output / "summary.json")
            if summary["interrupted"]:
                message = "TheMealDB fetch was interrupted."
            elif summary["failed_letters"]:
                letters = ", ".join(summary["failed_letters"])
                message = f"TheMealDB fetch failed for letter groups: {letters}."
            elif summary["skipped_records"]:
                message = "TheMealDB fetch skipped invalid recipes."
            else:
                message = "TheMealDB fetch returned an incomplete snapshot."
            return record_failed_run(url, run, "partial" if fetched else "failed", fetched, message)

        failure_message = "The fetched recipe snapshot could not be validated."
        recipe_rows, slots_by_meal = read_snapshot(output / "recipes.json")

        failure_message = "The recipe transaction or its run history could not be committed."
        with psycopg.connect(url, connect_timeout=10) as conn:
            inserted, updated, ingredients, slots, removed_slots = apply_snapshot(conn, recipe_rows, slots_by_meal)
            record_run(conn, run, "success", fetched, inserted=inserted, updated=updated)
    except KeyboardInterrupt:
        return record_failed_run(url, run, "failed", fetched, "Sync was interrupted.")
    except Exception as error:
        # Error text can contain credentials or source data. Keep only the error type.
        message = f"{failure_message} ({type(error).__name__})"
        # Reuse the run ID if the server committed before a connection failure was reported.
        return record_failed_run(url, run, "failed", fetched, message)

    LOG.info(
        "Synced %s recipes with %s inserted and %s updated. Added %s ingredients, "
        "%s ingredient slots inserted or updated, %s ingredient slots removed.",
        fetched, inserted, updated, ingredients, slots, removed_slots,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
