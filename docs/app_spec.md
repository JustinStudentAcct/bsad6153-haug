# Recipe Generator · Phase 1 Build Spec

## Overview

Help a busy household decide what to make for dinner and identify what it still
needs to buy. The primary user is the person choosing dinner for a family of
four. They should be able to open the app on a phone, browse meal ideas or
start with ingredients they have, choose a recipe, and review a shopping
checklist for that meal.

Phase 1 is the Week 4 web app. It recommends existing recipes from the
project's TheMealDB catalog in Supabase. The two required data views are
**Browse recipes** and **Match pantry ingredients**. Both lead to the same
recipe detail and shopping checklist. The app opens without a sign-in.

The project measures cumulative time spent deciding a week's dinners. The
overall target is under 30 minutes per week against a recorded baseline of
about 81 minutes. Keep measuring in the existing usage log during household
trials. This is an outcome to evaluate after use.

## User workflow and requirements

### Browse recipes

- Show a useful set of recipes on the initial screen. Let users search by
  partial recipe name and filter by a category from the database. Apply both
  criteria when both are set. Provide a way to clear them.
- Show the recipe name, category, and a thumbnail when available and cleared
  for display. Keep the recipe selectable if its image is missing or fails to
  load. Limit the number shown at once and let users reach more results.
- Give a clear next step when nothing matches, such as clearing the filters.
  Open the selected recipe from its card and preserve the user's search and
  filters when they return to the results.

### Match pantry ingredients

- Let users select one or more ingredients they already have from the
  database's ingredient list. Use searchable labels so they can find
  ingredients without knowing the source spelling in advance.
- Return recipes that contain every selected ingredient. Rank them by the
  fewest other distinct ingredient names, then by recipe name and source ID
  for stable ties. Show the number of other ingredients on each result.
- Match the existing normalized ingredient keys. Pantry choices track
  ingredient names, so a match does not confirm that the household has enough
  of each ingredient. Give users this context where they review the results.
- Explain how to start when nothing is selected. If all selected ingredients
  produce no matches, let the user remove selections and try again.

### Review a recipe and make a shopping checklist

- Show the recipe name, available photo, category, cooking instructions,
  ingredient names and measures, and the original source link when provided.
- Preserve source ingredient order and measures, including text such as
  “For frying.” If a measure is missing, keep the ingredient visible and mark
  the quantity for review. Keep repeated ingredient slots separate if the
  source lists them separately.
- Let users mark ingredients they already have and show the remaining items
  in a shopping checklist for the selected recipe. Preselect matching pantry
  ingredients when a recipe was opened from pantry results. Let the user
  reverse those selections and see the list update. If an ingredient appears
  more than once, marking it as on hand excludes all of its slots. Show a
  clear message when the checklist is empty.
- Keep pantry selections and checklist edits in the current session. Supabase
  persists the recipe catalog and sync history. Opening a new session loads
  the same catalog with fresh selections.

## Platform, deployment, and licensing

- Extend the existing Python and Streamlit app. Deploy it as a Render web
  service using the repository's blueprint and capture the HTTPS URL for
  course testing. Remove the placeholder sign-in from the Phase 1 experience
  and let reviewers use the full workflow without credentials.
- Query the Supabase PostgreSQL catalog through the server-side, read-only
  `APP_DATABASE_URL`. Use parameterized queries. The scheduled ingestion
  process continues to update the catalog independently of the app. Browsing,
  pantry matching, and recipe details all use the persisted catalog.
- Show the last successful sync using `sync_runs`. If the catalog is stale
  and readable, keep it available and show its freshness status. If the
  database is unavailable, show a retry message distinct from an empty result,
  and log sanitized diagnostics on the server.
- Use a mobile-first layout with a single-column flow at phone widths.
  Use light and dark grays, readable contrast, visible keyboard focus, and
  labeled controls. Make status clear through text as well as any color.
  Use system fonts or fonts licensed for free web use.
- Use dependencies, fonts, and assets with no paid license requirements.
  Show TheMealDB credit in the app and preserve supplied notices and recipe
  source links. Check third-party image rights before display and use a
  text-only card where image use is unclear.
- TheMealDB documents free access for educational and development use and
  recommends a supporter key for public shipping. Confirm that the planned
  unauthenticated Render course demo and scheduled ingestion fit the intended
  use before sharing the URL. Raise any unresolved permission, attribution,
  or service cost in the implementation plan. Record hosting costs and
  limits separately from license requirements.
  [TheMealDB API guide](https://www.themealdb.com/documentation) and
  [terms of use](https://www.themealdb.com/terms_of_use.php).

## Scope for later phases

- Week 5 adds natural-language recipe discovery and follow-up refinement using
  the same database. Week 6 adds the course agent workflow. The scaffold
  requires sign-in for features that spend money or take actions.
- Later product work may include saved favorites or meal plans, household
  profiles, user-submitted recipes, live pantry inventory, serving scaling,
  and combining shopping lists across meals.
- Grocery pricing, product matching, availability, and Kroger cart integration
  are stretch goals. The first checklist uses recipe measures as provided.

## Acceptance criteria

| Scenario | Expected result |
| --- | --- |
| Open the Render URL in a private browser window | Browse, pantry matching, recipe detail, and the checklist are accessible without a password. A fresh session retrieves recipes from Supabase. |
| Search by part of a recipe name and set a category | Results satisfy both criteria. Clearing the criteria restores browsing. Opening and returning from a recipe retains the active criteria. |
| Select eggs, rice, and garlic in the pantry view | Every result uses all three catalog ingredients. Results are ordered by the number of other distinct ingredients. The result agrees with reference question Q2 for the same data. |
| Open Acaraje and mark garlic and salt as on hand | The checklist omits garlic and salt, retains both red onion entries and their measures in source order, and restores an item when its selection is reversed. See Q3. |
| Open a recipe with a populated ingredient and a missing measure | The ingredient remains visible and the app flags the quantity for review. See Q4 for candidate recipes. |
| Try a search with no matches, a missing image, and a database outage | Search offers a reset, the recipe remains selectable without its photo, and the outage shows a separate retry message. A stale but readable catalog stays browsable. |
| Complete the workflow at a narrow phone width and a desktop width | Controls and instructions are readable and usable without horizontal scrolling. The same actions are available at both widths. |
| Review the deployed app and its credit | The app credits TheMealDB, supplies source links where available, and includes any other required notices. No paid license is needed for the chosen assets or dependencies. |

Reference questions and expected query behavior are documented in
[decision questions](decision_questions.md) and [SQL queries](../db/queries.sql).

## Implementation plan

1. Map the browse, pantry, and recipe detail screens to the existing
   `recipes`, `ingredients`, `recipe_ingredients`, and `sync_runs` tables.
   Reuse the reference queries when defining the application queries.
2. Build browsing and recipe detail as one end-to-end path with actual
   Supabase data. Verify it with the application reader role.
3. Add pantry matching and the one-recipe checklist. Compare the key cases
   against Q2, Q3, and Q4. Exercise filter reset, restoring checklist items,
   and missing data.
4. Check the phone and desktop layouts, freshness and error states, and
   attribution. Verify course-demo data and image use, confirm the planned
   Render and Supabase costs or limits, and flag anything that needs a
   decision.
5. Deploy to Render and repeat the acceptance checks in a fresh browser
   session. Record the deployed URL and test evidence in the Week 4
   verification notes. Log actual household trials in the usage log.
