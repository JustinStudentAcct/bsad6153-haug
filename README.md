# BSAD 6153 Project: Meal Recommendations and Ingredient Shopping

**Student:** Justin Haug
**My decision:** I want to decide what meals to prepare based on my preferences and available ingredients, and what ingredients I need to buy.
**Website:** &lt;your domain, from Week 4&gt;

The planned web app will help users discover recipes, choose meals, and build an ingredient shopping
list. Users will be able to exclude ingredients they already have from the shopping list. Grocery
product and pricing integration is a future goal; its API access and data-use permissions still need
to be confirmed.

The current recipe source is [TheMealDB](https://www.themealdb.com/). As of October 30, 2026, the project
has retrieved 790 unique recipes through first-letter searches from `a` through `z`. Raw API responses
and the combined recipe collection are stored locally in `data/raw/`, which Git ignores. Field
definitions and data-use notes are documented in [the data dictionary](docs/data_dictionary.md).

This repository is one complete AI system, built over eight weeks: a real API, synced on a schedule into a
PostgreSQL database, shown on a public website, with a chatbot and an agent that answer and act from your
own data. You build it with an AI coding agent, and you read and verify everything it writes.

---

## Setting up your computer (Week 1 Setup)

You need a **Windows 10/11 or macOS computer where you can install software**, Git, Python 3.12, and your AI
coding agent (Claude Code, Codex, Antigravity, or Copilot). Let your agent help with the installs, but read
every command before you approve it, and keep auto-approve off.

1. **Clone this repository** into a short folder path that isn't synced by OneDrive or Dropbox, for example
   `C:\dev\bsad6153` on Windows or `~/dev/bsad6153` on macOS.
2. **Create and activate a virtual environment** from the project folder:

   | | Windows (PowerShell) | macOS (Terminal) |
   |---|---|---|
   | Create | `py -3.12 -m venv .venv` | `python3.12 -m venv .venv` |
   | Activate | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |

   You'll see `(.venv)` at the start of your prompt when it's active. Activate it every time you open a new terminal.
3. **Install the packages:** `pip install -r requirements.txt`
4. **Create your secrets file:** copy `.env.example` to `.env`, and put a fake value on the `TEST_SECRET=` line.
5. **Check everything:** `python scripts/check_setup.py` should end with `Setup OK`.
6. **Try the website:** `streamlit run app/streamlit_app.py` opens it in your browser. Press Ctrl+C to stop it.

### Working with your AI agent

- **You approve every command.** Read it first, and if you don't understand it, ask the agent what it does.
- **Ask for a plan before code:** "Before writing anything, tell me your plan."
- **Never paste a real key into the chat,** and never ask the agent to print your `.env` file.
- **The agent never gets the owner database password or deploy tokens.** That's how agents delete databases.
- **Record what you directed, read, verified, and decided** in each pull request's AI review log.

---

## Project layout

| Folder | What goes there | When |
|---|---|---|
| `ingest/` | Fetch, load, and sync code | Weeks 1&ndash;3 |
| `db/` | `schema.sql`, `roles.sql`, `queries.sql` | Weeks 2&ndash;6 |
| `docs/` | Data dictionary, logs, reports (see `docs/README.md`) | Every week |
| `evals/` | Golden questions and evaluation runs | Weeks 3&ndash;7 |
| `app/` | Your website (Streamlit) | Weeks 4&ndash;6 |
| `examples/` | A reference tool-using chatbot loop | Week 5 |
| `scripts/` | Setup and database checks | Weeks 0&ndash;2 |
| `data/sample/` | A small sample of raw API data (large downloads go in `data/raw/`, which Git ignores) | Week 1 |

## Secrets: where each one lives

| Secret | On your computer | On Render (website) | In GitHub Actions (sync) |
|---|---|---|---|
| `DATABASE_URL` (owner) | `.env` | **never** | Actions secret |
| `APP_DATABASE_URL` (read-only) | `.env` | environment setting | if your checks need it |
| `AGENT_DATABASE_URL` | `.env` | environment setting | no |
| LLM key, `APP_PASSWORD` | `.env` | environment setting | no |
| Data API key | `.env` | no | Actions secret |

`.env.example` lists the names only. If a secret ever leaks, revoke or rotate it first, then tell the instructor.

---

## Deploying on Render (Week 4)

1. Claim your free domain through the GitHub Student Developer Pack.
2. In Render, choose **New &gt; Blueprint**, pick this repository, and enter each secret when asked.
   (`render.yaml` describes the service.) Or create a **Web Service** by hand with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run app/streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
   - Environment variables: `PYTHON_VERSION=3.12.4`, `APP_DATABASE_URL`, and later your LLM key and `APP_PASSWORD`
3. Under **Settings &gt; Custom Domains**, add your domain, then add the DNS records Render shows you at your
   registrar. Ask your agent to explain each record before you add it. HTTPS turns on automatically.
4. Free services sleep when idle and take about a minute to wake. Say so on your site.

---

## Troubleshooting

- **`pip install` fails with "No such file or directory" on Windows:** the folder path is too long. Move the
  project to a short path such as `C:\dev\bsad6153` and recreate `.venv`.
- **PowerShell says running scripts is disabled when you activate:** use Command Prompt instead and run
  `.venv\Scripts\activate.bat`, or ask the instructor. Don't change system security settings without asking.
- **`python` opens the Microsoft Store or isn't found:** use `py -3.12` on Windows or `python3.12` on macOS.
- **The database check can't connect:** use Supabase's Session pooler string, check the password, and check
  that your Supabase project isn't paused.

---

## Project proposal (Week 1)
My chosen API is from TheMealDB at https://www.themealdb.com/api/json/v1/ and my backup will be from Edamam at https://developer.edamam.com/meal-planner-api. The decision I chose was what to have for dinner. There are 4 people in my family, all members now being old enough to have an opinion, but only 2.5 people capable of cooking a family meal. The family has traditionally enjoyed picking meals by way of doom scrolling through the meals offered by meal delivery services. Those services cost more than they would if you did the meal planning yourself, but we as a family came to enjoy the images as meal ideas and the convenience. Ideally, I wanted to retain the images of meals as part of the recommendation, but if that proved too difficult, the text-only recommendation engine would still be of value. Chatbot integration is expected to be used as a means of entering and refining search criteria when the user requests a meal recommendation and reviews its ingredients. For example, I would ask the chatbot- "show me pasta meals for dinner." Then, upon seeing the results, I could further refine with, "show me only those that have a meat." Then, I would want the meal that's decided to have its ingredients presented in a list for review. The user could then uncheck what ingredients they already have on hand. Finally, then the human-in-the-loop-reviewed ingredients list could be moved to the Kroger cart integration for purchase and pickup. Regarding the agent's actions on my behalf, it will of course be leveraged to semantically search conversational text and backend data, but more importantly, it will allow the data to move when it can't do so programmatically. I do not anticipate rate limits to be much of a risk given the app is intended for personal use only. If it were to go to a live production environment for public use, the rate limits would be a concern. Additionally, key expiration is less of a concern given the free tier. Similarly, data volume is not a concern given the personal use expectation. Finally, the biggest risk with terms changing is with the data provider being bought out or simply no longer existing.

<!-- About 300 words: data source and backup API, your decision and workflow (from your baseline log),
     your first agent idea, and risks. See the Week 1 page. -->

## How to run this project

Fetch recipes from scratch using the project's virtual environment:

```powershell
.venv/Scripts/python.exe ingest/fetch.py
```

Each run queries `a` through `z` and writes original responses, combined recipes, a summary,
and a log to a new timestamped folder under `data/raw/`. See [ingestion instructions](ingest/README.md)
for pacing, retry handling, and output details.

<!-- Keep this current: how to run the sync, the website, and the evaluations. -->

## Credits

Recipe data: [TheMealDB](https://www.themealdb.com/). See its
[API documentation](https://www.themealdb.com/documentation) and
[terms of use](https://www.themealdb.com/terms_of_use.php). Recipe records retain their original source
links where provided.

<!-- Your data API's required attribution, plus any open-source code or samples you used. -->
