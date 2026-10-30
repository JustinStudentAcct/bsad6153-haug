"""Offline checks for fresh runs, pacing, retries, and incomplete downloads."""

import json
import string
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

import fetch


def response(status=200, payload=None, headers=None):
    result = requests.Response()
    result.status_code = status
    result.headers.update(headers or {})
    result._content = json.dumps(payload).encode("utf-8")
    return result


def meals(letter):
    return [
        {"idMeal": f"{letter}{index}", "strMeal": f"Meal {letter}{index}",
         "strInstructions": "Mix and cook."}
        for index in range(20)
    ]


class FetchTests(unittest.TestCase):
    @patch("fetch.time.sleep")
    def test_fresh_run_retries_paces_deduplicates_and_continues_after_empty_letter(self, sleep):
        replies = []
        for letter in string.ascii_lowercase:
            if letter == "b":
                replies.append(response(429, {"error": "rate limit"}, {"Retry-After": "7"}))
            if letter == "c":
                replies.append(requests.Timeout("test timeout"))
            if letter == "d":
                replies.append(response(503, {"error": "temporarily unavailable"}))
            records = None if letter == "x" else meals(letter)
            if letter == "a":
                records += [records[0], {"strMeal": "Missing required fields"}]
            replies.append(response(payload={"meals": records}))
        session = Mock()
        session.get.side_effect = replies
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            summary = fetch.collect(session, output)
            saved = json.loads((output / "recipes.json").read_text(encoding="utf-8"))["meals"]
            self.assertTrue(summary["complete"])
            self.assertEqual(len(saved), 500)
            self.assertEqual(len({meal["idMeal"] for meal in saved}), 500)
            self.assertEqual(summary["counts_by_letter"]["x"], 0)
            self.assertIn("z", summary["counts_by_letter"])
            self.assertEqual(summary["duplicate_records"], 1)
            self.assertEqual(len(summary["skipped_records"]), 1)
            self.assertEqual(len(summary["failures"]), 3)
            self.assertEqual((output / "response_b_1.body").read_bytes(), replies[1].content)
        self.assertEqual(session.get.call_count, 29)
        sleeps = [call.args[0] for call in sleep.call_args_list]
        self.assertIn(7, sleeps)
        self.assertEqual(sleeps.count(1.0), 28)

    @patch("fetch.time.sleep")
    def test_permanent_failure_is_reported_without_losing_other_letters(self, sleep):
        session = Mock()
        session.get.side_effect = [
            response(403, {"error": "forbidden"}) if letter == "b"
            else response(payload={"meals": meals(letter)})
            for letter in string.ascii_lowercase
        ]
        with tempfile.TemporaryDirectory() as directory:
            summary = fetch.collect(session, Path(directory))
            self.assertFalse(summary["complete"])
            self.assertEqual(summary["failed_letters"], ["b"])
            self.assertEqual(summary["unique_recipe_count"], 500)
            self.assertIn("z", summary["counts_by_letter"])
        self.assertEqual(session.get.call_count, 26)


if __name__ == "__main__":
    unittest.main()
