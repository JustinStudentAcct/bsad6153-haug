"""Offline checks for rejecting incomplete and invalid sync snapshots."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import fetch
import sync
from test_fetch import response


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("sync.load_dotenv"))
        self.enterContext(patch.dict(os.environ, {"DATABASE_URL": "test-dsn", "GITHUB_EVENT_NAME": ""}))
        self.connect = self.enterContext(patch("sync.psycopg.connect"))
        self.conn = self.connect.return_value.__enter__.return_value

    def test_rejects_incomplete_or_skipped_fetch_before_reading_snapshot(self):
        for interrupted, skipped_records, fetched, status in (
            (True, [], 0, "failed"), (False, [{"letter": "a"}], 500, "partial"),
        ):
            with self.subTest(status=status):
                self.connect.reset_mock()
                summary = {
                    "complete": not interrupted, "interrupted": interrupted,
                    "failed_letters": [], "skipped_records": skipped_records,
                    "unique_recipe_count": fetched,
                }
                with (
                    patch("sync.fetch_snapshot", return_value=(Path("snapshot"), summary)),
                    patch("sync.read_snapshot") as read_snapshot,
                    patch("sync.apply_snapshot") as apply_snapshot,
                    self.assertLogs("sync", level="ERROR") as logs,
                ):
                    self.assertEqual(sync.main(), 1)
                read_snapshot.assert_not_called()
                apply_snapshot.assert_not_called()
                self.connect.assert_called_once()
                _, params = self.conn.execute.call_args.args
                self.assertEqual(params[3:7], (status, fetched, 0, 0))
                self.assertEqual(params[-1], "manual")
                self.assertIn("summary.json", logs.output[0])

    def test_complete_fetch_passes_normalized_rows_to_transaction(self):
        meal = {
            "idMeal": "123",
            "strMeal": "Test meal",
            "strCategory": "Vegetarian",
            "strCountry": "Test country",
            "strInstructions": "Mix and cook.",
            "strIngredient1": "  red   onion  ",
        }
        summary = {"complete": True, "skipped_records": [], "unique_recipe_count": 1}

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            snapshot = output / "recipes.json"
            with (
                patch("sync.fetch_snapshot", return_value=(output, summary)),
                patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}),
                patch("sync.apply_snapshot", return_value=(1, 0, 1, 1, 0)) as apply_snapshot,
            ):
                snapshot.write_text(json.dumps({"meals": [meal]}), encoding="utf-8")
                with self.assertLogs("sync", level="INFO") as logs:
                    self.assertEqual(sync.main(), 0)
                self.assertIn("1 inserted and 0 updated", logs.output[0])
                self.connect.assert_called_once_with("test-dsn", connect_timeout=10)
                conn, recipes, slots = apply_snapshot.call_args.args
                self.assertIs(conn, self.conn)
                self.assertEqual(recipes[0][0], "123")
                self.assertEqual(slots, {"123": [(1, "red onion", None)]})
                _, params = conn.execute.call_args.args
                self.assertEqual(params[3:], ("success", 1, 1, 0, None, "schedule"))

                self.connect.reset_mock()
                apply_snapshot.reset_mock()
                meal["strCountry"] = " "
                snapshot.write_text(json.dumps({"meals": [meal]}), encoding="utf-8")
                with self.assertLogs("sync", level="ERROR") as logs:
                    self.assertEqual(sync.main(), 1)
                self.assertIn("could not be validated", logs.output[0])
                apply_snapshot.assert_not_called()
                self.connect.assert_called_once()
                _, params = self.conn.execute.call_args.args
                self.assertEqual(params[3:7], ("failed", 1, 0, 0))

    def test_error_details_are_excluded_from_run_history(self):
        secret = "secret connection password"
        with (
            patch("sync.fetch_snapshot", side_effect=OSError(secret)),
            self.assertLogs("sync", level="ERROR") as logs,
        ):
            self.assertEqual(sync.main(), 1)

        self.conn.execute.assert_called_once()
        _, params = self.conn.execute.call_args.args
        self.assertEqual(params[3:7], ("failed", 0, 0, 0))
        self.assertNotIn(secret, params[7])
        self.assertNotIn(secret, logs.output[0])

    @patch("fetch.time.sleep")
    def test_retry_exhaustion_records_failure_without_applying_recipes(self, sleep):
        session = Mock()
        session.get.side_effect = (
            [response(429, {}, {"Retry-After": "7"})] * 3
            + [response(503, {})] * 3
            + [response(payload={"meals": None})] * 24
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with (
                patch("sync.fetch_snapshot", side_effect=lambda: (output, fetch.collect(session, output))),
                patch("sync.apply_snapshot") as apply_snapshot,
                self.assertLogs(level="ERROR"),
            ):
                self.assertEqual(sync.main(), 1)
            apply_snapshot.assert_not_called()
            self.connect.assert_called_once()
            _, params = self.conn.execute.call_args.args
            self.assertEqual(params[3:7], ("failed", 0, 0, 0))
            self.assertIn("a, b", params[7])
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["failed_letters"], ["a", "b"])

        self.assertEqual(session.get.call_count, 30)
        delays = [call.args[0] for call in sleep.call_args_list if call.args[0] != 1.0]
        self.assertEqual(delays, [7, 7, 2, 4])
