# Week 4 app code tour

`app/streamlit_app.py` is the only app source file. It renders Browse,
Pantry, recipe details, and the session-only shopping checklist. It reads
the recipe catalog and sync history from Supabase.

Mark each row ✔ or ✘ after checking the linked lines yourself. Correct any
row marked ✘ in this file.

| Check | Claim to verify | Source | Student review |
| --- | --- | --- | --- |
| Local secret loading | `load_dotenv()` loads local environment values. The app checks whether `APP_DATABASE_URL` is present and reads its value only for the connection. | [L15](../app/streamlit_app.py#L15), [L27](../app/streamlit_app.py#L27), [L437](../app/streamlit_app.py#L437) | |
| Connection and role | `_read_catalog()` opens the connection, marks the transaction read-only, and checks `current_user`. A role other than `app_reader` raises an error before any catalog query runs. | [L27](../app/streamlit_app.py#L27), [L29](../app/streamlit_app.py#L29) | |
| Shared query execution and cache | Every data view calls `_read_catalog()`. It caches successful results for 600 seconds and passes SQL and parameters separately to `conn.execute()`. | [L17](../app/streamlit_app.py#L17), [L24](../app/streamlit_app.py#L24), [L31](../app/streamlit_app.py#L31) | |
| Freshness query | `_freshness_banner()` reads the latest successful `finished_at`. It shows the UTC timestamp, computes its age, and warns when it exceeds the configured limit. | [L39](../app/streamlit_app.py#L39), [L55](../app/streamlit_app.py#L55), [L64](../app/streamlit_app.py#L64) | |
| Browse queries | The app queries available categories and reads recipes using the selected category and partial name as parameters. | [L70](../app/streamlit_app.py#L70), [L113](../app/streamlit_app.py#L113) | |
| Pantry queries | The app reads ingredient options, then looks for recipes containing every selected key. It counts the other distinct ingredients to rank matches. | [L83](../app/streamlit_app.py#L83), [L155](../app/streamlit_app.py#L155) | |
| Recipe detail queries | The app uses the selected meal ID as a parameter for the recipe and its ingredient slots. It reads the slots in source order. | [L260](../app/streamlit_app.py#L260), [L274](../app/streamlit_app.py#L274) | |
| Checklist state | Checking an ingredient changes the current session's checklist for that meal. The grouped rows retain all measures. | [L300](../app/streamlit_app.py#L300), [L324](../app/streamlit_app.py#L324) | |
| Empty results and connection errors | Empty lists show a plain message. Database errors trigger friendly sync or catalog messages. The app disables detailed client error output. | [L34](../app/streamlit_app.py#L34), [L45](../app/streamlit_app.py#L45), [L224](../app/streamlit_app.py#L224), [L354](../app/streamlit_app.py#L354), [L467](../app/streamlit_app.py#L467) | |
| Public data | The SELECT queries read the fields for display and omit the raw source payload and sync error details. The catalog readers have no database write path. | [L41](../app/streamlit_app.py#L41), [L71](../app/streamlit_app.py#L71), [L262](../app/streamlit_app.py#L262) | |
