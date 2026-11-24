# Week 4 app code tour

`app/streamlit_app.py` is the only app source file. It renders Browse,
Pantry, recipe details, and the session-only shopping checklist. It reads
the recipe catalog and sync history from Supabase.

Mark each row ✔ or ✘ after checking the linked lines yourself. Correct any
row marked ✘ in this file.

| Check | Claim to verify | Source | Student review |
| --- | --- | --- | --- |
| Local secret loading | `load_dotenv()` loads local environment values. The app checks whether `APP_DATABASE_URL` is present and reads its value only for the connection. | [L16](../app/streamlit_app.py#L16), [L28](../app/streamlit_app.py#L28), [L461](../app/streamlit_app.py#L461) | ✔ |
| Connection and role | `_read_catalog()` opens the connection, marks the transaction read-only, and checks `current_user`. A role other than `app_reader` raises an error before any catalog query runs. | [L28](../app/streamlit_app.py#L28), [L30](../app/streamlit_app.py#L30) | ✔ |
| Shared query execution and cache | Every data view calls `_read_catalog()`. It caches successful results for 600 seconds and passes SQL and parameters separately to `conn.execute()`. | [L18](../app/streamlit_app.py#L18), [L25](../app/streamlit_app.py#L25), [L32](../app/streamlit_app.py#L32) | ✔ |
| Freshness query | `_freshness_banner()` reads the latest successful `finished_at`. It shows the UTC timestamp, computes its age, and warns when it exceeds the configured limit. | [L40](../app/streamlit_app.py#L40), [L56](../app/streamlit_app.py#L56), [L65](../app/streamlit_app.py#L65) | ✔ |
| Browse queries | The app queries available categories and reads recipes using the selected category and partial name as parameters. | [L71](../app/streamlit_app.py#L71), [L114](../app/streamlit_app.py#L114) | ✔ |
| Pantry queries | The app reads ingredient options, then looks for recipes containing every selected key. It counts the other distinct ingredients to rank matches. | [L84](../app/streamlit_app.py#L84), [L156](../app/streamlit_app.py#L156) | ✔ |
| Recipe detail queries | The app uses the selected meal ID as a parameter for the recipe and its ingredient slots. It reads the slots in source order. | [L279](../app/streamlit_app.py#L279), [L293](../app/streamlit_app.py#L293) | ✔ |
| Checklist state | Checking an ingredient changes the current session's checklist for that meal. The grouped rows retain all measures. | [L319](../app/streamlit_app.py#L319), [L343](../app/streamlit_app.py#L343) | ✔ |
| Empty results and connection errors | Empty lists show a plain message. Database errors trigger friendly sync or catalog messages. The app disables detailed client error output. | [L35](../app/streamlit_app.py#L35), [L46](../app/streamlit_app.py#L46), [L243](../app/streamlit_app.py#L243), [L373](../app/streamlit_app.py#L373), [L491](../app/streamlit_app.py#L491) | ✔ |
| Public data | The SELECT queries read the fields for display and omit the raw source payload and sync error details. The catalog readers have no database write path. | [L42](../app/streamlit_app.py#L42), [L72](../app/streamlit_app.py#L72), [L281](../app/streamlit_app.py#L281) | ✔ |
