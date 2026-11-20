"""Check each golden-question SQL reference as app_reader."""

import argparse
import csv
import json
import os
from datetime import UTC
from pathlib import Path

import psycopg
from dotenv import load_dotenv


QUESTIONS = Path(__file__).resolve().with_name("golden_questions.csv")
FIELDS = ["id", "question", "category", "reference_sql", "correct_behavior", "source"]
CATEGORIES = {"lookup", "aggregate", "trend", "compare", "should_decline"}


def read_questions(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        if reader.fieldnames != FIELDS:
            raise ValueError("The CSV header does not match the golden-question columns.")

        questions = []
        for number, row in enumerate(reader, 1):
            if None in row or any(row[field] is None for field in FIELDS):
                raise ValueError(f"CSV question {number} must have six fields.")

            row = {field: row[field].strip() for field in FIELDS}
            expected_id = f"Q{number:02d}"
            if row["id"] != expected_id:
                raise ValueError(f"Expected ID {expected_id} for question {number}.")
            if row["category"] not in CATEGORIES or row["source"] not in {"baseline", "other"}:
                raise ValueError(f"{expected_id} has an invalid category or source.")
            if not row["question"] or not row["correct_behavior"]:
                raise ValueError(f"{expected_id} needs a question and expected behavior.")
            requires_sql = row["category"] != "should_decline"
            if bool(row["reference_sql"]) != requires_sql:
                raise ValueError(f"{expected_id} must have SQL only if it is answerable.")
            questions.append(row)

    baseline = sum(row["source"] == "baseline" for row in questions)
    declines = sum(row["category"] == "should_decline" for row in questions)
    if len(questions) < 15 or baseline < 8 or declines < 3:
        raise ValueError("The CSV needs at least 15 questions, 8 baseline questions, and 3 declines.")
    return questions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save-answers", type=Path, help="Save the live reference results as JSON.")
    parser.add_argument("--compare-to", type=Path, help="Report IDs whose answers differ from a saved JSON file.")
    args = parser.parse_args()
    if args.save_answers and args.compare_to and args.save_answers.resolve() == args.compare_to.resolve():
        parser.error("Use a different path for the new answers and the comparison baseline.")

    try:
        questions = read_questions(QUESTIONS)
    except (OSError, ValueError, csv.Error) as error:
        print(f"[FAIL] Could not read golden questions. {error}")
        return 1

    load_dotenv(QUESTIONS.parents[1] / ".env")
    url = os.getenv("APP_DATABASE_URL")
    if not url:
        print("[FAIL] APP_DATABASE_URL is not set. Use the app_reader connection string.")
        return 1

    capture_answers = bool(args.save_answers or args.compare_to)
    answers = {}
    passed = failed = skipped = 0
    try:
        with psycopg.connect(url, connect_timeout=10) as conn:
            conn.read_only = True
            conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            with conn.transaction():
                role, captured_at = conn.execute("select current_user, transaction_timestamp()").fetchone()
                if role != "app_reader":
                    print("[FAIL] APP_DATABASE_URL must connect as app_reader.")
                    return 1
                conn.execute("set local statement_timeout = '10s'")
                conn.execute("set local time zone 'UTC'")
                print(f"Checking {len(questions)} questions as app_reader.")

                for row in questions:
                    question_id = row["id"]
                    if row["category"] == "should_decline":
                        print(f"[SKIP] {question_id} is a decline case.")
                        skipped += 1
                        continue

                    try:
                        with conn.transaction():
                            result = conn.execute(row["reference_sql"])
                            columns = [column.name for column in result.description or ()]
                            rows = []
                            if columns:
                                rows = result.fetchall() if capture_answers else result.fetchmany(1)
                    except psycopg.Error as error:
                        print(f"[FAIL] {question_id} query error ({error.sqlstate or type(error).__name__}).")
                        failed += 1
                        continue

                    if not rows:
                        print(f"[FAIL] {question_id} returned no rows.")
                        failed += 1
                        continue
                    if capture_answers:
                        answers[question_id] = {"columns": columns, "rows": rows}
                    print(f"[PASS] {question_id} returned at least one row.")
                    passed += 1
    except psycopg.Error as error:
        print(f"[FAIL] Could not use APP_DATABASE_URL ({error.sqlstate or type(error).__name__}).")
        return 1

    print(f"Reference queries: {passed} passed, {failed} failed. Decline cases: {skipped} skipped.")
    if failed:
        return 1

    if capture_answers:
        snapshot = {"captured_at_utc": captured_at.astimezone(UTC).isoformat(), "answers": answers}
        serialized = json.dumps(snapshot, indent=2, ensure_ascii=False, default=str) + "\n"
        try:
            if args.compare_to:
                baseline = json.loads(args.compare_to.read_text(encoding="utf-8"))["answers"]
                current = json.loads(serialized)["answers"]
                if not isinstance(baseline, dict) or baseline.keys() != current.keys():
                    raise ValueError("The saved baseline and current run must have the same question IDs.")
                changed = [question_id for question_id in current if current[question_id] != baseline[question_id]]
                print(f"Changed reference answers: {', '.join(changed) or 'none'}.")
            if args.save_answers:
                args.save_answers.parent.mkdir(parents=True, exist_ok=True)
                args.save_answers.write_text(serialized, encoding="utf-8")
                print(f"Saved answers to {args.save_answers}.")
        except (OSError, TypeError, KeyError, ValueError) as error:
            print(f"[FAIL] Could not save or compare answers. {error}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
