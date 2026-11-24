# Week 4 app verification

Local checks on November 23–24, 2026 used the Streamlit app and its
configured Supabase catalog. The app connected as `app_reader` in a
read-only transaction.

## Three displayed numbers

On November 24, I ran the SQL directly against Supabase and compared the
results with the local app pointed at the same catalog.

| App state | Supabase result | App display |
|---|---:|---|
| Browse with no search or category filter | 790 | 790 recipes |
| Browse with Chicken selected and no search | 80 | 80 recipes |
| Pantry with eggs, rice, and garlic selected | 9 | Tavë Kosi Baked Lamb and Yogurt · Other ingredients: 9 |

```sql
select count(*) from public.recipes;

select count(*) from public.recipes where category = 'Chicken';
```

For the Pantry number, run [query 2](../db/queries.sql) as written and read
`other_ingredients` on its first row. All three values matched.

## Other checks

| Check | Observed result |
|---|---|
| Browse and search | Category results matched the catalog. A partial, mixed-case search for Carbonara found Spaghetti alla Carbonara. Search and category worked together. |
| Pantry ranking | Eggs, rice, and garlic produced the same recipes and counts, in the same order, as the Milestone 2 reference query. |
| Acaraje checklist | Marking garlic and salt as on hand matched the reference shopping list and preserved both red onion ingredient lines. |
| Pagination | Changing either picker updated the recipe cards and the other picker. Changing a filter reset the results to page 1. On `milestone-3`, **Random** worked from both ends of the results, selected a different page, and stayed within the eight Chicken result pages when filtered. |
| Mobile layout | Search and Category fit side by side at 320 px and 390 px. The Page picker and Random button fit side by side at 320 px. Recipe cards opened by click or keyboard. |
| Photos | The project owner confirmed the Carbonara photo loaded. The renderer accepted all 790 stored image URLs in the snapshot. |
| Freshness and failures | The sync text appeared to the left of the three-dot menu on desktop and at 320 px. The displayed minute, 10:58 UTC on November 24, matched the successful `sync_runs.finished_at` value of `2026-11-24 10:58:59.976065+00`. Lowering the threshold for a test produced the stale warning. Earlier simulations covered database failures, retries, and empty results. |

## Public Render check

On November 24, [Meal Ideas on Render](https://bsad6153-haug.onrender.com/)
opened without sign-in, displayed the last successful sync in the toolbar,
and included the free-tier wake-up note. The live app displayed 790 total
recipes, 80 Chicken recipes, and 9 additional ingredients for the first
eggs, rice, and garlic Pantry match. Searching for Acaraje and selecting
its card opened the checklist. Checking red onions moved both measures
to **On hand**.

At the time of the check, GitHub's `main` was at `0cc038f`. The Random
controls were tested locally and pushed to `milestone-3` in `ff1e8f6`.
They require a merge to `main` and a Render deploy to appear on the site.

## Read-only proof

Using the local app's Supabase credentials, `select current_user;`
returned `app_reader`. In a separate transaction that allowed writes, this
zero-row probe returned SQLSTATE `42501` (`permission denied for table
recipes`). The transaction was rolled back.

```sql
update public.recipes set name = name where false;
```

The deployed app returned catalog results through code that checks for
`app_reader`. The separate write-permission probe using the deployed
connection string still needs to be recorded.
