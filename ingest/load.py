"""Load a saved TheMealDB recipes.json into the Milestone 2 schema."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


ROOT = Path(__file__).resolve().parents[1]


def optional_text(meal, field):
    value = meal.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text or null.")
    return value.strip() or None


def read_snapshot(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    meals = payload.get("meals") if isinstance(payload, dict) else None
    if not isinstance(meals, list) or not meals:
        raise ValueError("Expected a JSON object with a nonempty meals list.")

    recipe_rows = []
    slots_by_meal = {}
    for meal in meals:
        if not isinstance(meal, dict):
            raise ValueError("Each meal must be a JSON object.")
        meal_id = optional_text(meal, "idMeal")
        if not meal_id or not meal_id.isascii() or not meal_id.isdecimal():
            raise ValueError("Each meal must have a numeric TheMealDB idMeal string.")
        if meal_id in slots_by_meal:
            raise ValueError(f"Duplicate idMeal in snapshot: {meal_id}.")

        modified = optional_text(meal, "dateModified")
        if modified:
            modified = datetime.fromisoformat(modified)
            if modified.tzinfo is not None:
                raise ValueError(f"Meal {meal_id}: dateModified includes an unexpected offset.")
        recipe_rows.append((
            meal_id,
            optional_text(meal, "strMeal"),
            optional_text(meal, "strCategory"),
            optional_text(meal, "strCountry"),
            optional_text(meal, "strArea"),
            optional_text(meal, "strInstructions"),
            optional_text(meal, "strMealThumb"),
            optional_text(meal, "strSource"),
            modified,
            Jsonb(meal),
        ))

        slots = []
        for slot in range(1, 21):
            ingredient = optional_text(meal, f"strIngredient{slot}")
            measure = optional_text(meal, f"strMeasure{slot}")
            if ingredient:
                name = " ".join(ingredient.split())
                slots.append((slot, name, measure))
            elif measure:
                raise ValueError(f"Meal {meal_id}: slot {slot} has a measure without an ingredient.")
        slots_by_meal[meal_id] = slots

    return recipe_rows, slots_by_meal


def insert_snapshot(conn, recipe_rows, slots_by_meal):
    with conn.cursor() as cursor:
        # Stable key order lets concurrent loads acquire conflicting rows in the same order.
        cursor.executemany(
            """
            insert into public.recipes (
                meal_id, name, category, country, area, instructions,
                image_url, source_url, source_modified_at, raw_payload
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (meal_id) do nothing
            returning meal_id, recipe_id
            """,
            sorted(recipe_rows, key=lambda row: row[0]),
            returning=True,
        )
        new_recipes = dict(row for result in cursor.results() for row in result.fetchall())

        # Existing recipes keep both their original payload and their original slots.
        ingredients = {}
        slot_rows = []
        for meal_id, recipe_id in new_recipes.items():
            for slot, name, measure in slots_by_meal[meal_id]:
                key = name.casefold()
                ingredients.setdefault(key, name)
                slot_rows.append((recipe_id, slot, key, measure))

        if not slot_rows:
            return len(new_recipes), 0, 0

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
            insert into public.recipe_ingredients (recipe_id, slot_number, ingredient_key, measure)
            values (%s, %s, %s, %s)
            """,
            slot_rows,
        )
        return len(new_recipes), added_ingredients, cursor.rowcount


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="Path to a combined recipes.json from ingest/fetch.py")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        parser.exit(1, "DATABASE_URL is not set. Add the Session pooler URI to .env.\n")

    try:
        recipe_rows, slots_by_meal = read_snapshot(args.snapshot)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Could not read recipe snapshot: {error}\n")

    try:
        with psycopg.connect(url, connect_timeout=10) as conn:
            recipes, ingredients, slots = insert_snapshot(conn, recipe_rows, slots_by_meal)
    except psycopg.Error as error:
        detail = error.diag.message_primary or "Check the connection with scripts/check_db.py."
        parser.exit(1, f"Database load failed ({type(error).__name__}): {detail}\n")

    print(f"Inserted {recipes} recipes, {ingredients} ingredients, and {slots} recipe ingredient slots.")


if __name__ == "__main__":
    main()
