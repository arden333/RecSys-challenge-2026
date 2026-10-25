"""Export turn-level diagnostics for public development-set predictions.

Ground-truth responses, goals, and progress assessments are analysis-only fields.
They must not be used as features when producing recommendations.
"""

import argparse
import json
from pathlib import Path

import pyarrow.parquet as parquet

from metrics import compute_recsys_metrics


CODE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CODE_DIR.parent


def read_parquet_rows(directory: Path, prefix: str) -> list[dict]:
    paths = sorted(directory.glob(f"{prefix}-*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No {prefix} Parquet files in {directory}")
    return [row for path in paths for row in parquet.read_table(path).to_pylist()]


def index_by_turn(rows: list[dict], label: str) -> dict[tuple[str, int], dict]:
    indexed = {}
    for row in rows:
        key = (row["session_id"], row["turn_number"])
        if key in indexed:
            raise ValueError(f"Duplicate {label} turn: {key}")
        indexed[key] = row
    return indexed


def one_message(conversations: list[dict], turn_number: int, role: str) -> dict:
    matches = [
        message
        for message in conversations
        if message["turn_number"] == turn_number and message["role"] == role
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one {role} message at turn {turn_number}, found {len(matches)}"
        )
    return matches[0]


def export_turn_analysis(task_id: str) -> tuple[Path, int]:
    if Path(task_id).name != task_id:
        raise ValueError("Task ID must be a file name, not a path")

    prediction_path = CODE_DIR / "exp" / "inference" / "devset" / f"{task_id}.json"
    truth_path = CODE_DIR / "exp" / "ground_truth" / "devset.json"
    predictions = json.loads(prediction_path.read_text(encoding="utf-8"))
    ground_truth = json.loads(truth_path.read_text(encoding="utf-8"))
    prediction_by_turn = index_by_turn(predictions, "prediction")
    truth_by_turn = index_by_turn(ground_truth, "ground truth")
    if prediction_by_turn.keys() != truth_by_turn.keys():
        missing = truth_by_turn.keys() - prediction_by_turn.keys()
        extra = prediction_by_turn.keys() - truth_by_turn.keys()
        raise ValueError(f"Prediction/ground-truth turn mismatch: {len(missing)} missing, {len(extra)} extra")

    sessions = read_parquet_rows(PROJECT_DIR / "data" / "Dataset", "test")
    session_by_id = {session["session_id"]: session for session in sessions}
    if len(session_by_id) != len(sessions):
        raise ValueError("Duplicate session IDs in the development set")

    tracks = read_parquet_rows(PROJECT_DIR / "data" / "Track-Metadata", "all_tracks")
    track_by_id = {track["track_id"]: track for track in tracks}
    if len(track_by_id) != len(tracks):
        raise ValueError("Duplicate track IDs in the all_tracks catalog")

    output_dir = CODE_DIR / "exp" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    detail_path = output_dir / f"{task_id}_turns.jsonl"

    with detail_path.open("w", encoding="utf-8") as detail_file:
        for key, truth in truth_by_turn.items():
            session_id, turn_number = key
            session = session_by_id[session_id]
            prediction = prediction_by_turn[key]
            if truth["user_id"] != session["user_id"] or prediction["user_id"] != session["user_id"]:
                raise ValueError(f"User ID mismatch at {key}")

            conversations = session["conversations"]
            user_query = one_message(conversations, turn_number, "user")["content"]
            ground_truth_response = one_message(conversations, turn_number, "assistant")["content"]
            previous_conversations = [
                {
                    "turn_number": message["turn_number"],
                    "role": message["role"],
                    "content": message["content"],
                }
                for message in conversations
                if message["turn_number"] < turn_number
            ]

            target_id = truth["ground_truth_track_id"]
            predicted_ids = prediction["predicted_track_ids"]
            top100_ids = prediction.get("retrieved_top100_track_ids")
            if top100_ids is not None:
                if len(top100_ids) != 100 or top100_ids[:20] != predicted_ids or len(set(top100_ids)) != 100:
                    raise ValueError(f"Invalid top-100 retrieval list at {key}")
            ranked_ids = top100_ids if top100_ids is not None else predicted_ids
            target_rank = ranked_ids.index(target_id) + 1 if target_id in ranked_ids else None
            scores = compute_recsys_metrics(predicted_ids, [target_id], [1, 10, 20])
            target_track = track_by_id[target_id]
            predicted_tracks = [track_by_id[track_id] for track_id in predicted_ids]
            goal = session["conversation_goal"]

            detail = {
                "session_id": session_id,
                "user_id": session["user_id"],
                "turn_number": turn_number,
                "session_date": session["session_date"],
                "user_profile": session["user_profile"],
                "conversation_goal": goal,
                "goal_progress_assessments": [
                    assessment
                    for assessment in session["goal_progress_assessments"]
                    if assessment["turn_number"] == turn_number
                ],
                "previous_conversations": previous_conversations,
                "user_query": user_query,
                "ground_truth_track_id": target_id,
                "ground_truth_track": target_track,
                "ground_truth_response": ground_truth_response,
                "predicted_track_ids": predicted_ids,
                "predicted_tracks": predicted_tracks,
                "ground_truth_rank": target_rank,
                "hit_at_20": int(target_rank is not None and target_rank <= 20),
                **scores,
            }
            if top100_ids is not None:
                detail["retrieved_top100_track_ids"] = top100_ids
                detail["hit_at_100"] = int(target_rank is not None)
            if "predicted_response" in prediction:
                detail["predicted_response"] = prediction["predicted_response"]
            detail_file.write(json.dumps(detail, ensure_ascii=False) + "\n")

    return detail_path, len(truth_by_turn)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tid", default="llama1b_bm25_devset", help="Development-set prediction file name without .json")
    args = parser.parse_args()
    detail, count = export_turn_analysis(args.tid)
    print(f"Exported {count} turns to {detail}")
