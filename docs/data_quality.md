# TheMealDB data quality and coverage

**Scope.** The first sections cover the saved October 30, 2026 TheMealDB run in `data/raw/themealdb_20261030T212358782687Z/`. I compared the 26 original first-letter responses with `recipes.json` and checked them against `summary.json`. The Milestone 3 sections report a later audit of the live database. Both audits describe the collected recipes. The full catalog and recipe accuracy are outside their scope.

## Collection and identifiers

| Check | Result |
| --- | --- |
| First-letter requests | 26 succeeded, with no recorded retries, failed letters, or skipped records |
| Recipe count | 790 records across the raw responses and 790 in the combined file. The records match in content and order. |
| Meal IDs | All 790 are unique, nonblank strings containing digits. No duplicate IDs occurred in the raw responses. |
| Recipe names | No exact duplicates after ignoring case and normalizing whitespace. Similar names or alternate versions can still refer to similar dishes. |
| Letter coverage | 25 letter queries returned recipes. The `x` query succeeded with no matches. The `s` response included Šúľance s Makom (ID `53187`), whose title starts with `Š`. Keep records returned by the API even if their names differ from the requested letter under a literal prefix check. |

The earlier October 30 collection contains the same 790 IDs and field values. These two runs establish agreement between the saved copies that day. A longer series would be needed to measure the API's update frequency.

## Field completeness

The denominator is 790 recipes. A field counts as missing when its key is absent, its value is JSON `null`, or its text is empty after trimming whitespace.

| Field | Missing | Share | Detail |
| --- | ---: | ---: | --- |
| `idMeal`, `strMeal`, `strCategory`, `strCountry`, `strInstructions` | 0 each | 0% | Present on every recipe in this run |
| `strMealThumb`, `strIngredient1`, `strMeasure1` | 0 each | 0% | Present on every recipe. Later ingredient slots can be empty. |
| `strSource` | 37 | 4.7% | 11 nulls and 26 empty strings |
| `strArea` | 190 | 24.1% | All 190 still have a country label |
| `strYoutube` | 198 | 25.1% | Empty strings |
| `dateModified` | 303 | 38.4% | All 487 populated values parse as timestamps without a timezone |
| `strTags` | 592 | 74.9% | Nulls |

A populated field establishes presence only. This audit did not verify links, cooking directions, or allergen information. For future refreshes, compare contents by `idMeal`. The missing timestamps and unspecified timezone make `dateModified` insufficient as the sole update signal.

## Ingredients and measures

Across the 20 numbered slots per recipe, there are 8,152 ingredient entries. Of those, 8,122 have a measure and **30 lack a measure**, affecting **10 recipes**. There are no measures without a corresponding ingredient. Another 7,648 slots have neither value. Those unused slots are expected in a fixed-width recipe format.

- **Missing quantity.** Alfajores (ID `53138`) lists dulce de leche in slot 7 without a measure. Keep the ingredient visible on a shopping list and ask the user to confirm the amount.
- **Free-text quantity.** The collection includes values such as `800g`, `1/2 cup`, and `For frying`. Keep the original measure when an amount and unit cannot be separated confidently.
- **Repeated ingredients.** 175 recipes repeat an ingredient name after case and whitespace normalization. Acaraje (ID `53483`) lists red onions twice, once diced and once sliced. Keep both slots in the recipe. Combining them for shopping requires checking quantities and units.

There are 946 distinct normalized ingredient names. That count describes spellings in the recipe data. It does not establish a catalog of unique ingredients or grocery products.

## Milestone 3 database audit

I ran [the SQL quality checks](../db/quality_checks.sql) as `app_reader` in one read-only Supabase snapshot on **November 20, 2026 at 20:07:59 UTC**. Query numbers below match the numbered comments in the SQL file. The October raw-response checks above use the original fetch artifacts.

### Row counts (query 1)

| Table | Rows on November 20, 2026 |
| --- | ---: |
| `recipes` | 790 |
| `ingredients` | 946 |
| `recipe_ingredients` | 8,152 |
| `sync_runs` | 5 |

### Missing values (query 2)

For source fields, missing includes null, absent, empty, and whitespace-only values. For stored measures, blank values have already been converted to SQL `NULL`.

| Field | Missing / total on November 20, 2026 | Missing rate |
| --- | ---: | ---: |
| `idMeal`, `strMeal`, `strCategory`, `strCountry`, `strInstructions` | 0 / 790 each | 0.0% |
| `strMealThumb`, `strIngredient1`, `strMeasure1` | 0 / 790 each | 0.0% |
| `strSource` | 37 / 790 | 4.7% |
| `strArea` | 190 / 790 | 24.1% |
| `strYoutube` | 198 / 790 | 25.1% |
| `dateModified` | 303 / 790 | 38.4% |
| `strTags` | 592 / 790 | 74.9% |
| `recipe_ingredients.measure` | 30 / 8,152 | 0.4% |

### Duplicates, anomalies, and orphans (queries 3–5)

| Check | Matches on November 20, 2026 |
| --- | ---: |
| Duplicate `meal_id`, duplicate `ingredient_key`, or duplicate `(recipe_id, slot_number)` groups | 0 each |
| Normalized recipe titles shared by different meal IDs | 0 |
| Recipes with an ingredient repeated in separate slots | 175 |
| Malformed meal IDs, slot numbers outside 1–20, or source edit dates after the UTC audit day | 0 each |
| Source measures with no ingredient in the same slot | 0 |
| Recipes with at least one missing measure | 10 |
| Recipes with no populated ingredient slots | 0 |
| Slots missing a recipe parent or an ingredient parent | 0 each |

The title check folds case and normalizes whitespace. Similar titles and alternate recipes can still describe the same dish. Foreign keys reject slots with missing parents. Deleting a recipe cascades to its slots, and a referenced ingredient cannot be deleted while slots still use it.

### Cleaning decisions

- **Cleaned.** Trim source text, turn blank optional fields into nulls, and collapse ingredient-name whitespace before case-folding the lookup key. This lets differently capitalized spellings match the same key while preserving a display name.
- **Rejected.** A sync with failed fetches or skipped invalid recipes cannot write recipe data. Validation also rejects malformed IDs, missing required recipe text, and measures paired with empty ingredient slots. This keeps an incomplete or internally inconsistent payload from overwriting the current data.
- **Preserved.** Keep alternate recipes by source ID, repeated ingredient slots in recipe order, and measures as source text after trimming. Leave missing quantities null. The wording can describe preparation as well as quantity, so combining duplicate slots or inferring amounts can change the shopping list.

## Coverage and fairness check

Queries 6–8 reproduced the October coverage results on **November 20, 2026**. The database had **63 country labels and 14 categories** on that date. Eleven country labels had five or fewer recipes. Category counts included 167 Dessert recipes (21.1%), 100 Vegetarian recipes, seven Vegan recipes, and two Goat recipes.

| Selected country labels | Recipes on November 20, 2026 | Missing `strArea` | Missing `strTags` |
| --- | ---: | ---: | ---: |
| United Kingdom | 59 | 0 | 10 |
| Spain | 48 | 0 | 44 |
| United States | 33 | 0 | 10 |
| Vietnam | 27 | 0 | 27 |
| Dominica | 16 | 16 | 16 |
| Cambodia | 15 | 15 | 15 |
| Brazil | 11 | 11 | 11 |
| Bahamas | 1 | 1 | 1 |

In the November 20 audit, the United Kingdom had 59 recipes and the Bahamas had one. A chatbot that treats those counts as cuisine popularity would draw a conclusion the catalog cannot support. Requiring `strArea` would exclude 190 recipes and erase **26 country labels** from results. Requiring `strTags` would exclude 592 recipes and erase **35 country labels**. For example, all 15 Cambodian recipes would disappear under either filter. Use the populated `strCountry` field for country lookups, and let general search match on names, categories, and ingredients even when tags are missing. Once the app ranks recipes, check which country labels appear for comparable queries.

## Milestone 3 pipeline checks

**Lineage.** TheMealDB's 26 first-letter responses feed `ingest/sync.py` through the fetcher's raw files and deduplicated snapshot. Validation trims text, checks required fields, parses optional `dateModified`, and pairs ingredients with the measures in their numbered slots. `recipes` retains the original meal object as JSONB as well as the normalized columns. `ingredients` stores whitespace-normalized names keyed by their case-folded values. `recipe_ingredients` preserves slot order, repeated entries, and free-text measures. The sync writes the outcome to `sync_runs`. See the [data dictionary](data_dictionary.md#sync-lineage) for the field mapping.

**Freshness.** With successful runs and a prompt API response, a newly visible source edit should be imported at the next six-hour scan, plus GitHub queue time and processing time. The worst case is unbounded during missed runs, paused services, prolonged outages, or source publication delays. Records that vanish from the API remain in the database. Check the latest successful run even when the change counts are zero. Partial snapshots are retained for diagnosis and do not change the recipe tables.

**Change log.** The first scheduled run checked 790 recipes and recorded zero inserts and zero updates. In the isolated recovery test, a changed ingredient measure was saved even though the reported `dateModified` did not change. The golden lookup for “Spaghetti Carbonara” also confirmed that the catalog uses the title “Spaghetti alla Carbonara.” That lookup accepts both names. See [sync test results](sync_tests.md) for the logged evidence and reference answer comparison.

**Ownership.** Data Engineering owns the ingestion and quality checks. Its on-call should receive workflow failure and stale-data alerts. Platform or Database Operations handles service, pooler, or credential incidents. The product data steward reviews missing fields and how the app describes coverage to users.
