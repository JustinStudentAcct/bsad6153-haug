# evals/

How you prove your system gives correct answers.

| Week | File | What it does |
|---|---|---|
| 3 | `golden_questions.csv` | 15+ questions with columns `id, question, category, reference_sql, correct_behavior, source` |
| 3 | `check_reference.py` | Runs every reference query as `app_reader` and checks that it returns at least one row |
| 5 | `run_evals.py` | Asks your chatbot every golden question; records answer, tool calls, tokens, cost, time, and the reference result |
| 5&ndash;7 | `results/weekN.csv` | One results file per evaluation run, graded by you |

Reference answers are SQL, not fixed values, because your data keeps syncing.

From the project root, run the reference check with `APP_DATABASE_URL` set in `.env`:

```powershell
.venv/Scripts/python.exe evals/check_reference.py
```

The checker skips `should_decline` rows. Their `correct_behavior` is evaluated in
the later chatbot and agent tests. The questions marked `baseline` come from the
[running meal-planning list](../docs/decision_questions.md), including the five
[business queries](../db/queries.sql). The fairness question draws on the
[coverage audit](../docs/data_quality.md#coverage-and-fairness-check).
