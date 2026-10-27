"""Check paired Exp03 recovery and loss accounting."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import compare_exp03_retrievers as comparison


def prediction(session_id: str, ranked_ids: list[str]) -> dict:
    return {
        "session_id": session_id,
        "turn_number": 1,
        "predicted_track_ids": ranked_ids[:20],
        "retrieved_top100_track_ids": ranked_ids,
    }


class Exp03ComparisonTests(unittest.TestCase):
    def test_embedding_only_and_bm25_only_are_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            predictions_dir = root / "inference"
            predictions_dir.mkdir()
            truth_path = root / "truth.json"
            truth_path.write_text(json.dumps([
                {"session_id": "s1", "turn_number": 1, "ground_truth_track_id": "target-a"},
                {"session_id": "s2", "turn_number": 1, "ground_truth_track_id": "target-b"},
            ]), encoding="utf-8")
            base_ids = [f"track-{index}" for index in range(100)]
            rows = {
                "bm25": [
                    prediction("s1", base_ids),
                    prediction("s2", ["target-b", *base_ids[:99]]),
                ],
                "qwen3": [
                    prediction("s1", ["target-a", *base_ids[:99]]),
                    prediction("s2", base_ids),
                ],
            }
            for name, file_name in comparison.PREDICTION_NAMES.items():
                (predictions_dir / f"{file_name}.json").write_text(
                    json.dumps(rows[name]), encoding="utf-8"
                )
            with patch.object(comparison, "PREDICTION_DIR", predictions_dir), patch.object(
                comparison, "GROUND_TRUTH_PATH", truth_path
            ):
                paired, summary = comparison.compare()
            self.assertEqual(len(paired), 2)
            self.assertEqual(summary["paired_vs_bm25"]["qwen3"]["at_100"]["embedding_only"], 1)
            self.assertEqual(summary["paired_vs_bm25"]["qwen3"]["at_100"]["bm25_only"], 1)
            self.assertEqual(paired[0]["qwen3_top20_track_ids"][0], "target-a")
            self.assertEqual(len(paired[0]["bm25_top100_track_ids"]), 100)


if __name__ == "__main__":
    unittest.main()
