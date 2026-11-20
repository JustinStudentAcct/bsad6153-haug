# Milestone 3 sync tests

## Interrupted run and recovery

I applied `db/schema.sql` and `db/sync_runs.sql` to a disposable PostgreSQL 16
database and seeded it with the Milestone 2 loader and the October 30 snapshot.
The starting tables contained 790 recipes, 946 ingredients, and 8,152 ingredient
slots. I replayed the saved HTTP responses through the real sync and fetcher. In
the `a` response, I simulated a source edit to Acaraje (`idMeal` `53483`) by
changing the first measure from `800g` to `800g (simulated source edit)` and
leaving `dateModified` unchanged. I raised `KeyboardInterrupt` as the fetcher
requested the second letter, after it had received 40 recipes.

The sync exited with code `1` and logged a `partial` run. A comparison of all
rows in the three recipe data tables showed that every value and timestamp
stayed the same. The next run replayed all 26 pages with the same simulated
edit and exited with code `0`. It updated Acaraje and its first ingredient slot
in place, preserving the IDs, `first_seen_at` values, and table row counts.
Only the edited recipe and slot changed. This also shows that the sync detects
a content change when the source's reported modification time stays the same.

## Back-to-back rerun

Immediately after recovery, I ran the same complete fixture again. The second
run exited with code `0` and logged **0 inserts and 0 updates**. All three data
tables matched their post-recovery state, including timestamps. The test runs
used a local database and a controlled HTTP replay.

### Resulting `sync_runs` rows

Times are UTC. The fixture changed a measure only, so the recovery counts that
as one updated recipe.

| Attempt | `run_id` | `started_at` | `finished_at` | `status` | Fetched | Inserted | Updated | `trigger` | `error_message` |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| Interrupted | `646a9751-53eb-4f24-a0d5-0cde56cbb6e5` | `2026-11-19 20:46:04.840108` | `2026-11-19 20:46:04.861747` | partial | 40 | 0 | 0 | manual | TheMealDB fetch was interrupted. |
| Recovered | `405dbaf9-17f5-418c-a536-a0ddf178771b` | `2026-11-19 20:46:05.000049` | `2026-11-19 20:46:05.261193` | success | 790 | 0 | 1 | manual | `NULL` |
| Rerun | `14f9dc14-c964-4852-aa97-f4985ff28436` | `2026-11-19 20:46:05.372674` | `2026-11-19 20:46:05.613287` | success | 790 | 0 | 0 | manual | `NULL` |

## Golden-question baseline and follow-up

The Part F check confirmed that all 12 SQL queries returned rows. It did not
save the returned values. I captured the first saved [live answer baseline](../evals/results/milestone3_reference_baseline.json)
as `app_reader` at **2026-11-19 20:43:02 UTC**. All 12 queries passed and six
decline cases were skipped. The baseline stores the column names and ordered
rows for Q01–Q12. An immediate check of the comparison command found no changed
answers.

**Follow-up.** The [first scheduled run](https://github.com/JustinStudentAcct/bsad6153-haug/actions/runs/44607023515)
finished on November 19 at 20:17:47 UTC, before the baseline. Three more scheduled
runs succeeded after the baseline, each fetching 790 recipes with zero inserts
and zero updates.

| Scheduled run | Finished in Supabase (UTC) | Fetched | Inserted | Updated |
| --- | --- | ---: | ---: | ---: |
| [44660318380](https://github.com/JustinStudentAcct/bsad6153-haug/actions/runs/44660318380) | 2026-11-20 02:23:29 | 790 | 0 | 0 |
| [44702895896](https://github.com/JustinStudentAcct/bsad6153-haug/actions/runs/44702895896) | 2026-11-20 08:30:01 | 790 | 0 | 0 |
| [44753297051](https://github.com/JustinStudentAcct/bsad6153-haug/actions/runs/44753297051) | 2026-11-20 14:26:26 | 790 | 0 | 0 |

I captured the [follow-up answers](../evals/results/milestone3_reference_followup.json)
as `app_reader` on November 20 at 19:02:28 UTC. All 12 SQL checks passed and six
decline cases were skipped. Only **Q12** changed. Its last successful sync moved
from November 19 at 20:17:47 UTC to November 20 at 14:26:26 UTC. Its seven-day
insert and update totals remained zero. Q01–Q11 still returned the same rows and
values, consistent with three scans that found no recipe changes. The isolated
source-edit test shows how a changed payload reaches the tables.

Check the eligible scheduled runs in Supabase with the following query.

```sql
select run_id, finished_at, records_fetched, records_inserted, records_updated
from public.sync_runs
where "trigger" = 'schedule'
  and status = 'success'
  and started_at > timestamptz '2026-11-19 20:43:02.488865+00'
order by finished_at;
```

To reproduce the comparison from the project root, run the following command.

```powershell
.\.venv\Scripts\python.exe evals/check_reference.py `
  --compare-to evals/results/milestone3_reference_baseline.json `
  --save-answers evals/results/milestone3_reference_followup.json
```

The command compares the latest answers and verifies that every SQL reference
still returns rows. The saved follow-up file is the evidence from November 20.
