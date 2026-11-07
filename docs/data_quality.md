# TheMealDB data quality and coverage

**Scope.** This report measures the saved October 30, 2026 TheMealDB run in `data/raw/themealdb_20261030T212358782687Z/`. I compared the 26 original first-letter responses with `recipes.json` and checked them against `summary.json`. The report covers the recipes returned by those searches. It does not measure the full TheMealDB catalog or verify the accuracy of the recipes.

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

## Coverage and fairness check

The collection spans **63 country labels and 14 categories**. The three most represented country labels are the United Kingdom (59), Spain (48), and the United States (33). Eleven labels have five or fewer recipes, including the Bahamas with one. Category counts range from 167 Dessert recipes (21.1% of the snapshot) and 100 Vegetarian recipes to seven Vegan recipes and two Goat recipes. These counts describe the source collection and cannot establish how representative it is of any cuisine or diet.

| Selected country labels | Recipes | Missing `strArea` | Missing `strTags` |
| --- | ---: | ---: | ---: |
| United Kingdom | 59 | 0 | 10 |
| Spain | 48 | 0 | 44 |
| United States | 33 | 0 | 10 |
| Vietnam | 27 | 0 | 27 |
| Dominica | 16 | 16 | 16 |
| Cambodia | 15 | 15 | 15 |
| Brazil | 11 | 11 | 11 |
| Bahamas | 1 | 1 | 1 |

A search that requires `strArea` would exclude 190 recipes and all recipes from **26 of the 63 country labels**. Requiring `strTags` would exclude 592 recipes and all recipes from **35 labels**. For country filtering, use the populated `strCountry` field. For general search, let recipes match on their names, categories, and ingredients even when tags are missing. Once the app ranks recipes, check which country labels appear in results for comparable queries. This report measures differences in source coverage and metadata completeness. It does not measure the fairness of an implemented ranking system.
