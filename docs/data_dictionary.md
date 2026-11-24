## **Source:** 
  - API Name: TheMealDB
  - Base URL: https://www.themealdb.com/api/json/v1/
  - Endpoints Used: https://www.themealdb.com/api/json/v1/1/search.php?f=a. We did one request for each of the 26 letters then combined the requests afterwards.
  - Documentation: https://www.themealdb.com/documentation#v1
  - Terms: https://www.themealdb.com/terms_of_use.php
  - Authentication Method: API key directly in the URL path

## **What one record means:** 
Each record is its own unique recipe, containing its name, category, often an image, ingredients, ingredient quantities, and instructions

## **Fields:** 
Here are the most important fields and their information:

| Name | Type | Example | What it means | nullable |
| --- | --- | --- | --- | --- |
| idMeal | string despite appearing as a whole number | 53483 | its just an ID | no |
| strMeal | string | Acaraje black-eyed pea fritters with shrimp filling | descriptive name | no |
| strCategory | string | Seafood | Recipe category used to group and filter meals | none observed in 790 recipes |
| strArea | string or null | Turkish | Cuisine or regional label; can be absent even when strCountry is populated | yes |
| strCountry | string | Brazil | Country associated with the recipe | none observed in 790 recipes |
| strInstructions | string | Make the filling by placing the onion, ginger, garlic, chilli, and some salt into food processor. (excerpt) | Cooking directions stored as one text field, which can contain multiple steps and line breaks | none observed in 790 recipes |
| strIngredient1 | string | Black Eyed Peas | First ingredient; numbered ingredient fields run from strIngredient1 through strIngredient20 | none observed for this first slot; later slots can be empty |
| strMeasure1 | string | 800g | Amount or preparation text for strIngredient1; each numbered measure pairs with the ingredient of the same number | none observed for this first slot; later slots can be empty |
| strMealThumb | string or null | `https://www.themealdb.com/images/media/meals/…jpg` | Recipe photo URL stored as `recipes.image_url` | none observed in the October snapshot |
| strSource | string or null | https://www.bbcgoodfood.com/recipes/caraje-black-eyed-pea-fritters-shrimp-filling | URL of the original recipe source | yes; null or empty string |
| strTags | string or null | Pudding | Optional descriptive tags; multiple tags can be stored in a comma-separated string | yes |
| dateModified | timestamp text or null | `2026-10-30 13:00:00` (example format) | Source-reported edit time stored without a time zone as `recipes.source_modified_at` | yes; missing for 303 of 790 October records |

## **Identifiers and relationships:**
The source identifies a meal by `idMeal`. PostgreSQL stores it as the unique `recipes.meal_id` and assigns an internal `recipe_id`. Ingredient names from the recipe payload become keys in `ingredients`, and `(recipe_id, slot_number)` identifies each `recipe_ingredients` row. Category remains text on `recipes`. All three tables come from the meal search endpoint.

## Sync lineage

1. **TheMealDB → `ingest/fetch.py`.** GitHub Actions or a manual run starts `ingest/sync.py`. The fetcher requests `search.php?f=` for `a` through `z`, saves raw responses and a summary, and combines recipes by `idMeal`, keeping the first occurrence. The summary records empty letter responses as successful requests.
2. **Snapshot → `ingest/load.py` validation.** The sync rejects incomplete fetches and skipped records. The loader verifies numeric meal IDs and required text, trims text, treats blank optional text as null, and parses `dateModified` as a timestamp without a time zone when present. The source does not document a reliable change filter, so the full payload is used to detect edits.
3. **Validated meals → `recipes`.** Upsert on `meal_id`. Map the meal name, category, country, area, instructions, photo, source URL, and reported edit time to columns. Keep the source object in `raw_payload` as JSONB. Existing records keep their internal ID and `first_seen_at`. `last_updated_at` advances when the JSONB payload changes.
4. **Numbered ingredients → `ingredients` and `recipe_ingredients`.** Pair each ingredient and measure by slot number. Collapse whitespace in ingredient names and case-fold to get `ingredient_key`. Keep the first stored display spelling. Store populated slots in recipe order, preserve repeated names in separate slots, and keep measures as trimmed text or null. Upsert changed slots and remove slots omitted from a changed recipe. Keep shared ingredients and recipes absent from a full fetch.
5. **Run outcome → `sync_runs`.** A successful run commits the recipe and slot changes and its audit row in one transaction. A completed partial or failed attempt records its status and zero committed recipe changes separately when the database is reachable. The row stores start and finish times, trigger, unique recipes fetched, recipe insert and update counts, and a sanitized error if applicable.

## Freshness

The Milestone 3 tests used a six-hour schedule. The current schedule runs weekly. If TheMealDB exposes an edit just after its letter was fetched and the next run succeeds, the edit normally arrives within roughly one week plus GitHub queue time and sync runtime. There is no guaranteed maximum age. GitHub can delay or miss a run, Supabase can pause, and API or database failures can block refreshes until a successful run. Source publication lag is outside the pipeline's control. The sync also retains meals that disappear from the source, so their stored contents can persist indefinitely. Use the last successful `sync_runs.finished_at` to measure pipeline freshness.

## Milestone 3 change log

The database now compares entire meal payloads. A recipe can be updated even if `dateModified` stays the same. The first scheduled scan fetched 790 recipes and found zero inserts or updates. Its successful completion still advanced the freshness timestamp. See [sync test results](sync_tests.md) for the interruption, recovery, and no-change rerun.

## Ownership

In a company, Data Engineering would own the fetch, schema, quality checks, and recovery. The ingestion on-call should receive GitHub Actions failure alerts and investigate stale runs. Platform or Database Operations should handle Supabase availability, credentials, and pooler access. The product data steward should decide how to present missing or unverified recipe information.

## **Suprises:**
This probably shouldn't surprise me, but I was expecting a value for dateModified on each record, but just over half actually had them.

## **Data-use ethics check:**
- **Terms:** TheMealDB permits copying, storing, and modifying content obtained through official API endpoints for development use, but prohibits website scraping and API resale without permission; app-store publication requires paid access, and artwork attribution, existing notices, and third-party content rights must be respected. Commercial deployment would require reviewing the applicable access terms rather than assuming unrestricted permission.
- **PII concerns:** These records describe recipes, not people. Note that the API's attribution to recipes via links may ultimately lead to the original recipe author's information, that they are likely to have self-published.
- **Worst Case Leak:** Disclosure of these already-public recipes would present little privacy risk. But not requiring a leak, the greatest liability is inaccurate ingredient quantities or missing allergen information, which could cause harm if users treated the stored data as complete and reliable.
- **Data Access:** visitors could read recipe information, while only the administrator and authorized import process could change the shared recipe records; users could manage their own recipes and meal plans without altering the source collection.
