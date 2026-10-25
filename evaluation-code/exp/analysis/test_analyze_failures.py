import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import analyze_failures


class AnalyzeFailuresTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.input_path = Path(self.temp_dir.name) / "sample_turns.jsonl"
        records = [
            {
                "session_id": "session-1",
                "turn_number": 1,
                "user_query": "Find rainy music",
                "conversation_goal": {"category": "G", "specificity": "LH"},
                "ground_truth_rank": None,
                "ndcg@20": 0.0,
                "hit_at_20": 0,
                "ground_truth_track": {"track_name": ["Target 1"], "artist_name": ["Artist"]},
                "predicted_tracks": [{"track_name": ["Guess 1"], "artist_name": ["Artist"]}],
            },
            {
                "session_id": "session-2",
                "turn_number": 2,
                "user_query": "Find upbeat music",
                "conversation_goal": {"category": "J", "specificity": "HH"},
                "ground_truth_rank": 1,
                "ndcg@20": 1.0,
                "hit_at_20": 1,
                "ground_truth_track": {"track_name": ["Target 2"], "artist_name": ["Artist"]},
                "predicted_tracks": [{"track_name": ["Target 2"], "artist_name": ["Artist"]}],
            },
        ]
        self.input_path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        self.report_path = self.input_path.with_name("sample_failure_report.md")

    def run_script(self, *arguments):
        output = io.StringIO()
        with patch.object(sys, "argv", ["analyze_failures.py", "--input", str(self.input_path), *arguments]):
            with contextlib.redirect_stdout(output):
                analyze_failures.main()
        return output.getvalue()

    def test_default_run_writes_markdown_report(self):
        terminal_output = self.run_script()
        report = self.report_path.read_text(encoding="utf-8")

        self.assertIn("Saved report to", terminal_output)
        self.assertNotIn("Find rainy music", terminal_output)
        self.assertIn("## Overall", report)
        self.assertIn("| 2 | 0.500 | 0.500 |", report)
        self.assertIn("| missing_top20 | 1 |", report)
        self.assertIn("### session-1 — turn 1", report)
        self.assertIn("- Predicted #1: Guess 1 — Artist", report)

    def test_filters_change_saved_report(self):
        self.run_script("--category", "J", "--outcome", "rank_1")
        report = self.report_path.read_text(encoding="utf-8")

        self.assertIn("| 1 | 1.000 | 1.000 |", report)
        self.assertIn("### session-2 — turn 2", report)
        self.assertNotIn("session-1", report)

    def test_no_matches_still_writes_report(self):
        self.run_script("--category", "Z")
        report = self.report_path.read_text(encoding="utf-8")

        self.assertIn("No turns match these filters.", report)
        self.assertNotIn("## Overall", report)


if __name__ == "__main__":
    unittest.main()
