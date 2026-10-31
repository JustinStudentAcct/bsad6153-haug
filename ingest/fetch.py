"""Fetch TheMealDB recipes from a through z into a fresh data/raw/ folder.

Run from the project root: .venv/Scripts/python.exe ingest/fetch.py
Uses the public educational key 1; no private credentials are needed.
"""

import json
import logging
import math
import string
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://www.themealdb.com/api/json/v1/1/search.php"
MAX_ATTEMPTS = 3
REQUEST_DELAY = 1.0
LOG = logging.getLogger(__name__)


def retry_delay(response, attempt):
    """Use exponential backoff, honoring longer Retry-After seconds or dates."""
    delay = 2 ** attempt
    value = response.headers.get("Retry-After") if response is not None else None
    if value:
        try:
            requested = float(value)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
                requested = (retry_at - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                LOG.warning("Invalid Retry-After header; using exponential backoff")
                return delay
        if math.isfinite(requested):
            delay = max(delay, requested)
    return delay


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def collect(session, output):
    """Start with no prior data; preserve partial results even if interrupted."""
    recipes = {}
    summary = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": API_URL,
        "attempts": 0,
        "counts_by_letter": {},
        "failed_letters": [],
        "failures": [],
        "skipped_records": [],
        "duplicate_records": 0,
        "interrupted": False,
    }
    try:
        # This API has no numbered pages: traverse its documented letter groups.
        for letter in string.ascii_lowercase: #string.ascii_lowercase contains abcdefghijklmnopqrstuvwxyz
            successful = False
            for attempt in range(1, MAX_ATTEMPTS + 1):
                # Pace every request, including retries, after the preceding one.
                if summary["attempts"]:
                    time.sleep(REQUEST_DELAY)
                summary["attempts"] += 1
                response = None
                try:
                    response = session.get(
                        API_URL, params={"f": letter}, timeout=(10, 30), #That produces requests ending in ?f=a, then ?f=b, and so on.
                        allow_redirects=False,
                    )
                    # Preserve original bytes; error bodies may not actually be JSON.
                    suffix = "json" if response.status_code == 200 else "body"
                    (output / f"response_{letter}_{attempt}.{suffix}").write_bytes(response.content)
                    if response.status_code != 200:
                        raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
                    payload = response.json()
                    if not isinstance(payload, dict) or "meals" not in payload:
                        raise ValueError("Missing meals field")
                    meals = payload["meals"]
                    if meals is None:
                        meals = []
                    if not isinstance(meals, list):
                        raise ValueError("Expected meals list or null")
                    for index, meal in enumerate(meals):
                        required = ("idMeal", "strMeal", "strInstructions")
                        missing = [key for key in required if not isinstance(meal, dict) or not meal.get(key)]
                        if missing:
                            summary["skipped_records"].append(
                                {"letter": letter, "index": index, "missing_fields": missing}
                            )
                            LOG.warning("Letter %s record %s skipped: missing %s", letter, index, missing)
                            continue
                        meal_id = str(meal["idMeal"])
                        if meal_id in recipes:
                            summary["duplicate_records"] += 1
                        else:
                            recipes[meal_id] = meal
                    summary["counts_by_letter"][letter] = len(meals)
                    successful = True
                    LOG.info("Letter %s: %s returned; %s unique recipes total", letter, len(meals), len(recipes))
                    break
                except (requests.RequestException, ValueError) as exc:
                    summary["failures"].append(
                        {"letter": letter, "attempt": attempt, "error": str(exc)}
                    )
                    LOG.warning("Letter %s, attempt %s/%s: %s", letter, attempt, MAX_ATTEMPTS, exc)
                    status = response.status_code if response is not None else None
                    # Retry timeouts, connection errors, malformed JSON, 429 and 5xx.
                    if status is not None and status != 200 and status != 429 and status < 500:
                        break
                    if attempt < MAX_ATTEMPTS:
                        delay = retry_delay(response, attempt)
                        LOG.info("Backing off for %.1f seconds before retry", delay)
                        time.sleep(delay)
            if not successful:
                summary["failed_letters"].append(letter)
                LOG.error("Letter %s could not be retrieved; continuing", letter)
    except KeyboardInterrupt:
        summary["interrupted"] = True
        LOG.warning("Interrupted; saving partial results")
    finally:
        summary["finished_at"] = datetime.now(timezone.utc).isoformat()
        summary["unique_recipe_count"] = len(recipes)
        summary["all_letters_retrieved"] = len(summary["counts_by_letter"]) == 26
        summary["minimum_500_met"] = len(recipes) >= 500
        summary["complete"] = (
            summary["all_letters_retrieved"] and summary["minimum_500_met"]
            and not summary["interrupted"]
        )
        write_json(output / "recipes.json", {"meals": list(recipes.values())})
        write_json(output / "summary.json", summary)
    return summary


def main():
    output = ROOT / "data" / "raw" / (
        "themealdb_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    )
    output.mkdir(parents=True, exist_ok=False)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(output / "run.log", encoding="utf-8")],
    )
    LOG.info("Starting fresh. Output: %s", output)
    with requests.Session() as session:
        session.headers["User-Agent"] = "BSAD6153-classroom-ingest/1.0"
        summary = collect(session, output)
    LOG.info(
        "Finished: %s unique recipes; %s/26 letters; %s failed requests; %s skipped records",
        summary["unique_recipe_count"], len(summary["counts_by_letter"]),
        len(summary["failures"]), len(summary["skipped_records"]),
    )
    LOG.info("Results saved in %s", output)
    if not summary["complete"]:
        LOG.error("Run incomplete; see summary.json for details")
    return 0 if summary["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
