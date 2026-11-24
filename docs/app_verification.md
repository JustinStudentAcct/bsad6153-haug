# Week 4 app verification

Local checks on November 23, 2026 used the Streamlit app and its configured
Supabase catalog. The app connected as `app_reader` in a read-only
transaction.

| Check | Observed result |
|---|---|
| Browse and search | Category results matched the catalog. A partial, mixed-case search for Carbonara found Spaghetti alla Carbonara. Search and category worked together. |
| Pantry ranking | Eggs, rice, and garlic produced the same recipes and counts, in the same order, as the Milestone 2 reference query. |
| Acaraje checklist | Marking garlic and salt as on hand matched the reference shopping list and preserved both red onion ingredient lines. |
| Pagination | Changing either page picker updated the recipe cards and the other picker. Changing a filter reset the results to page 1. |
| Mobile layout | Search and Category fit side by side at 320 px and 390 px. Recipe titles and thumbnails had equal outer spacing on desktop and at 390 px. The recipe button opened the detail view. |
| Photos | The project owner confirmed the Carbonara photo loaded. The renderer accepted all 790 stored image URLs in the snapshot. |
| Freshness and failures | The browser showed the last successful sync in the footer. Simulated stale data, database failures, retries, and empty results produced the expected messages. |

The local checks did not test every remote photo response or a Render
deployment. The Week 4 rubric expects freshness at the top of the page.
The current app shows it in the footer at the project owner's request.
