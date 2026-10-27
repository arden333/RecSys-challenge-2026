"""Measure complete Exp03 retrieval inputs with each model's tokenizer."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

from datasets import load_dataset
from omegaconf import OmegaConf
from transformers import AutoTokenizer

from mcrs.db_item import MusicCatalogDB


MODEL_LIMITS = {"bge_m3": 8192, "qwen3": 32768}


def track_document(track: dict, fields: list[str]) -> str:
    lines = []
    for field in fields:
        value = track[field]
        if isinstance(value, list):
            value = ", ".join(value)
        lines.append(f"{field}: {value}")
    return "\n".join(lines) + "\n"


def retrieval_queries(sessions, item_db: MusicCatalogDB):
    for session in sessions:
        conversations = session["conversations"]
        for turn_number in range(1, 9):
            history = []
            for message in conversations:
                if message["turn_number"] >= turn_number:
                    continue
                content = message["content"]
                role = message["role"]
                if role == "music":
                    role = "assistant"
                    content = item_db.id_to_metadata(content)
                history.append({"role": role, "content": content})
            user_messages = [
                message["content"] for message in conversations
                if message["turn_number"] == turn_number and message["role"] == "user"
            ]
            if len(user_messages) != 1:
                raise ValueError(f"Expected one user message at {session['session_id']} turn {turn_number}")
            history.append({"role": "user", "content": user_messages[0]})
            query = "\n".join(f"{message['role']}: {message['content']}" for message in history)
            yield turn_number, query


def token_lengths(tokenizer, texts, batch_size: int = 128):
    for start in range(0, len(texts), batch_size):
        batch = tokenizer(
            texts[start:start + batch_size],
            add_special_tokens=True,
            truncation=False,
            padding=False,
            return_length=True,
        )
        yield from batch["length"]


def summarize(lengths: list[int], supported_length: int, configured_length: int) -> dict:
    ordered = sorted(lengths)
    return {
        "count": len(lengths),
        "min": ordered[0],
        "median": median(ordered),
        "mean": round(mean(ordered), 2),
        "p90": ordered[int(0.9 * (len(ordered) - 1))],
        "max": ordered[-1],
        "over_model_limit": sum(length > supported_length for length in lengths),
        "over_configured_length": sum(length > configured_length for length in lengths),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODEL_LIMITS, required=True)
    args = parser.parse_args()

    code_dir = Path(__file__).resolve().parent
    config = OmegaConf.load(code_dir / "config" / f"exp03_{args.model}_devset.yaml")
    fields = list(config.corpus_types)
    item_db = MusicCatalogDB(
        str((code_dir / config.item_db_name).resolve()),
        list(config.track_split_types), fields,
    )
    sessions = load_dataset(str((code_dir / config.test_dataset_name).resolve()), split="test")
    queries_by_turn = defaultdict(list)
    for turn_number, query in retrieval_queries(sessions, item_db):
        if args.model == "qwen3":
            query = f"Instruct: {config.retrieval_query_instruction}\nQuery:{query}"
        queries_by_turn[turn_number].append(query)
    documents = [track_document(track, fields) for track in item_db.metadata_dict.values()]

    tokenizer = AutoTokenizer.from_pretrained(
        config.retrieval_model_name, cache_dir=str(code_dir / "cache/hf"), use_fast=True
    )
    supported_length = MODEL_LIMITS[args.model]
    configured_length = config.retrieval_max_length
    by_turn = {
        turn: summarize(list(token_lengths(tokenizer, queries)), supported_length, configured_length)
        for turn, queries in queries_by_turn.items()
    }
    all_query_lengths = [
        length for queries in queries_by_turn.values()
        for length in token_lengths(tokenizer, queries)
    ]
    doc_lengths = list(token_lengths(tokenizer, documents))
    print(json.dumps({
        "model": config.retrieval_model_name,
        "instruction": config.get("retrieval_query_instruction"),
        "model_limit": supported_length,
        "configured_max_length": configured_length,
        "queries": summarize(all_query_lengths, supported_length, configured_length),
        "documents": summarize(doc_lengths, supported_length, configured_length),
        "queries_by_turn": by_turn,
    }, indent=2))


if __name__ == "__main__":
    main()
