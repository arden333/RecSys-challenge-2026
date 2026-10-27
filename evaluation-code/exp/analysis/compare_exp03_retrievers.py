"""Compare Exp01 BM25 and Exp03 Qwen3 retrieval on the same development turns."""

import json
import math
from collections import defaultdict
from pathlib import Path


ANALYSIS_DIR = Path(__file__).resolve().parent
EVALUATION_DIR = ANALYSIS_DIR.parent.parent
PREDICTION_DIR = EVALUATION_DIR / "exp/inference/devset"
GROUND_TRUTH_PATH = EVALUATION_DIR / "exp/ground_truth/devset.json"
PREDICTION_NAMES = {
    "bm25": "custom_exp01_bm25_tags_devset_top100",
    "qwen3": "custom_exp03_qwen3_devset_top100",
}


def turn_key(row: dict) -> tuple[str, int]:
    return row["session_id"], row["turn_number"]


def load_predictions(path: Path) -> dict[tuple[str, int], dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    indexed = {}
    for row in rows:
        key = turn_key(row)
        if key in indexed:
            raise ValueError(f"Duplicate prediction turn: {key}")
        top20 = row["predicted_track_ids"]
        top100 = row["retrieved_top100_track_ids"]
        if len(top20) != 20 or len(top100) != 100 or top100[:20] != top20:
            raise ValueError(f"Invalid top-20/top-100 predictions at {key}")
        if len(set(top100)) != 100:
            raise ValueError(f"Duplicate retrieved track at {key}")
        indexed[key] = row
    return indexed


def target_rank(row: dict, target_id: str) -> int | None:
    ranked_ids = row["retrieved_top100_track_ids"]
    return ranked_ids.index(target_id) + 1 if target_id in ranked_ids else None


def compare() -> tuple[list[dict], dict]:
    truth_rows = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    truth_by_turn = {turn_key(row): row for row in truth_rows}
    if len(truth_by_turn) != len(truth_rows):
        raise ValueError("Duplicate ground-truth turn")
    predictions = {
        name: load_predictions(PREDICTION_DIR / f"{file_name}.json")
        for name, file_name in PREDICTION_NAMES.items()
    }
    for name, by_turn in predictions.items():
        if by_turn.keys() != truth_by_turn.keys():
            raise ValueError(f"{name} predictions have mismatched development turns")

    rows = []
    for key, truth in truth_by_turn.items():
        target_id = truth["ground_truth_track_id"]
        row = {
            "session_id": key[0],
            "turn_number": key[1],
            "ground_truth_track_id": target_id,
        }
        for name, by_turn in predictions.items():
            rank = target_rank(by_turn[key], target_id)
            row[f"{name}_rank"] = rank
            row[f"{name}_hit_at_20"] = int(rank is not None and rank <= 20)
            row[f"{name}_hit_at_100"] = int(rank is not None)
            row[f"{name}_ndcg_at_20"] = (
                1 / math.log2(rank + 1) if rank is not None and rank <= 20 else 0.0
            )
            row[f"{name}_top20_track_ids"] = by_turn[key]["predicted_track_ids"]
            row[f"{name}_top100_track_ids"] = by_turn[key]["retrieved_top100_track_ids"]
        rows.append(row)

    summary = {"turns": len(rows), "models": {}, "paired_vs_bm25": {}, "by_turn": {}}
    for name in PREDICTION_NAMES:
        summary["models"][name] = {
            "hit_at_20": sum(row[f"{name}_hit_at_20"] for row in rows),
            "hit_at_100": sum(row[f"{name}_hit_at_100"] for row in rows),
            "mean_ndcg_at_20": sum(row[f"{name}_ndcg_at_20"] for row in rows) / len(rows),
        }
        if name == "bm25":
            continue
        summary["paired_vs_bm25"][name] = {}
        for k in (20, 100):
            bm25_field = f"bm25_hit_at_{k}"
            model_field = f"{name}_hit_at_{k}"
            summary["paired_vs_bm25"][name][f"at_{k}"] = {
                "both_hit": sum(row[bm25_field] and row[model_field] for row in rows),
                "bm25_only": sum(row[bm25_field] and not row[model_field] for row in rows),
                "embedding_only": sum(not row[bm25_field] and row[model_field] for row in rows),
                "both_miss": sum(not row[bm25_field] and not row[model_field] for row in rows),
            }

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["turn_number"]].append(row)
    for turn_number, turn_rows in sorted(grouped.items()):
        summary["by_turn"][turn_number] = {
            name: {
                "hit_at_20": sum(row[f"{name}_hit_at_20"] for row in turn_rows),
                "hit_at_100": sum(row[f"{name}_hit_at_100"] for row in turn_rows),
            }
            for name in PREDICTION_NAMES
        }
    return rows, summary


if __name__ == "__main__":
    compared_rows, comparison_summary = compare()
    output_path = ANALYSIS_DIR / "exp03_paired_turns.jsonl"
    with output_path.open("w", encoding="utf-8") as output:
        for row in compared_rows:
            output.write(json.dumps(row) + "\n")
    print(json.dumps(comparison_summary, indent=2))
    print(f"Saved paired turns to {output_path}")
