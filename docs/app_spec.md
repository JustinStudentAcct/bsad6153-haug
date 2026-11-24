# Recipe Generator · Week 4 app spec

## Audience and questions

I use the site first to decide what to cook for my family of four. A public
visitor should understand that this course demo finds dinner ideas in the
synced TheMealDB catalog and builds a shopping checklist for one recipe.

1. **Browse (Q01).** What chicken, pasta, or seafood dinners can I browse with
   photos? Filter by category. Show available, permitted photos and keep
   recipes selectable without one.
2. **Pantry (Q02).** If I have eggs, rice, and garlic, which recipes use all
   three and need the fewest other ingredients? Require every selected
   ingredient and rank by the count of other distinct ingredient names.
3. **Checklist (Q03).** What should I buy for Acaraje if I have garlic and
   salt? Show recipe instructions and ordered ingredients with measures.
   Let users exclude items they have. Preserve repeated lines, flag missing
   measures, and keep selections in the current session.

These questions use [SQL queries 1–3](../db/queries.sql),
[golden questions Q01–Q03](../evals/golden_questions.csv), and the
[baseline log](baseline_log.md) steps for meal ideas, pantry checks, and shopping.

## Database access and privacy

Connect to Supabase PostgreSQL only as `app_reader` through the server-side
`APP_DATABASE_URL`. Pass selections as SQL parameters. Never write to the
database or display secrets, raw errors, stack traces, or information
designated private by the [Milestone 1 ethics check](data_dictionary.md#data-use-ethics-check).

## Done when

- A banner at the top shows the latest successful `sync_runs.finished_at`
  and its age. Warn visibly after eight days or if no sync has succeeded.
  This allows one day for delays after the weekly sync is due.
- Browse and Pantry answer Q01 and Q02 using the Milestone 2 queries.
  Changing a selection changes the parameterized query. A recipe opened
  from either view supports the Q03 checklist.
- Empty results and database failures show distinct, plain messages.
  Users can clear their filters or retry after a database error.
- Use `st.cache_data(ttl=600)` for database reads. Explain in the README
  that 10 minutes is shorter than the weekly sync interval and balances
  stale results against repeated database queries.
- The Streamlit app runs on Render without sign-in and works on phones and
  desktops. Use grayscale, free or system fonts, and assets and dependencies
  requiring no paid licenses. Credit TheMealDB, include required notices,
  and confirm demo and image permissions before sharing the URL.

## Handoff

Have the assistant read `db/schema.sql`, `db/queries.sql`, and this spec,
then review its plan before it writes code. Limit app changes to `app/`.
Update the README TTL note separately if the cache behavior changes.
