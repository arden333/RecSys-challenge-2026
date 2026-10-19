import os
import json
import random
from collections import Counter
from pathlib import Path
from datasets import load_dataset, concatenate_datasets
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = PROJECT_ROOT / "data" / "Dataset"
INFERENCE_DIR = PROJECT_ROOT / "evaluation-code" / "exp" / "inference" / "devset"

def load_popularity_track():
    db = load_dataset(str(DATASET_DIR), split="train")
    track_ids = []
    for item in db:
        conversations = item['conversations']
        for turn in conversations:
            if turn['role'] == 'music':
                track_ids.append(turn['content'])
    track_ids = Counter(track_ids).most_common(20)
    popularity_track_ids = [track_id for track_id, _ in track_ids]
    return popularity_track_ids

def main():
    popularity_track_ids = load_popularity_track()
    db = load_dataset(str(DATASET_DIR), split="test")
    inference_results = []
    for item in tqdm(db):
        user_id = item['user_id']
        session_id = item['session_id']
        for target_turn_number in range(1, 9):
            inference_results.append({
                "session_id": session_id,
                "user_id": user_id,
                "turn_number": target_turn_number,
                "predicted_track_ids": popularity_track_ids,
                "predicted_response": ""
            })
    INFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with (INFERENCE_DIR / "popularity.json").open("w", encoding="utf-8") as f:
        json.dump(inference_results, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
