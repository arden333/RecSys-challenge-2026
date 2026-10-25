"""Inspect public development-set ranking failures from a turn-level JSONL file."""

import argparse
from pathlib import Path
from textwrap import shorten

import pandas as pd


DEFAULT_INPUT = Path(__file__).resolve().parent / "llama1b_bm25_devset_turns.jsonl"
OUTCOMES = ("missing_top20", "rank_11_20", "rank_2_10", "rank_1")
DEEP_OUTCOMES = ("rank_21_100", "missing_top100")


def track_label(track: dict | None) -> str:
    if not track:
        return "(no track)"
    names = "; ".join(track.get("track_name") or [])
    artists = "; ".join(track.get("artist_name") or [])
    return f"{names} — {artists}" if artists else names


def load_turns(path: Path) -> pd.DataFrame:
    rows = []
    for chunk in pd.read_json(path, lines=True, chunksize=500):
        for record in chunk.to_dict(orient="records"):
            rank = record["ground_truth_rank"]
            if pd.isna(rank) or rank > 20:
                outcome = "missing_top20"
            elif rank > 10:
                outcome = "rank_11_20"
            elif rank > 1:
                outcome = "rank_2_10"
            else:
                outcome = "rank_1"

            predicted_tracks = record["predicted_tracks"]
            goal = record["conversation_goal"]
            rows.append(
                {
                    "session_id": record["session_id"],
                    "turn_number": record["turn_number"],
                    "user_query": record["user_query"],
                    "goal_category": goal["category"],
                    "goal_specificity": goal["specificity"],
                    "ground_truth_rank": rank,
                    "ndcg@20": record["ndcg@20"],
                    "hit_at_20": record["hit_at_20"],
                    "hit_at_100": record.get("hit_at_100"),
                    "outcome": outcome,
                    "ground_truth_track": track_label(record["ground_truth_track"]),
                    "predicted_top3_tracks": [track_label(track) for track in predicted_tracks[:3]],
                }
            )
    return pd.DataFrame(rows)


def format_summary(turns: pd.DataFrame, group: str) -> str:
    has_top100 = turns["hit_at_100"].notna().all()
    aggregations = {
        "turns": ("session_id", "size"),
        "hit_at_20": ("hit_at_20", "mean"),
    }
    if has_top100:
        aggregations["hit_at_100"] = ("hit_at_100", "mean")
    aggregations["mean_ndcg_20"] = ("ndcg@20", "mean")
    summary = (
        turns.groupby(group, dropna=False)
        .agg(**aggregations)
        .reset_index()
    )
    if has_top100:
        lines = [f"| {group} | Turns | Hit@20 | Hit@100 | Mean nDCG@20 |", "| --- | ---: | ---: | ---: | ---: |"]
        for value, count, hit20, hit100, ndcg in summary.itertuples(index=False, name=None):
            lines.append(f"| {value} | {count} | {hit20:.3f} | {hit100:.3f} | {ndcg:.3f} |")
    else:
        lines = [f"| {group} | Turns | Hit@20 | Mean nDCG@20 |", "| --- | ---: | ---: | ---: |"]
        for value, count, hit, ndcg in summary.itertuples(index=False, name=None):
            lines.append(f"| {value} | {count} | {hit:.3f} | {ndcg:.3f} |")
    return "\n".join(lines)


def format_report(turns: pd.DataFrame, args: argparse.Namespace) -> str:
    lines = [
        "# Retrieval failure analysis",
        "",
        f"Source: {args.input.name}",
        "",
        f"Filters: category={args.category or 'all'}, specificity={args.specificity or 'all'}, "
        f"turn={args.turn or 'all'}, outcome={args.outcome}, example limit={args.limit}",
        "",
    ]
    if turns.empty:
        return "\n".join(lines + ["No turns match these filters.", ""])

    has_top100 = turns["hit_at_100"].notna().all()
    counts = turns["outcome"].value_counts().reindex(OUTCOMES, fill_value=0)
    if has_top100:
        overall_header = ["| Turns | Hit@20 | Hit@100 | Mean nDCG@20 |", "| ---: | ---: | ---: | ---: |"]
        overall_values = f"| {len(turns)} | {turns['hit_at_20'].mean():.3f} | {turns['hit_at_100'].mean():.3f} | {turns['ndcg@20'].mean():.3f} |"
    else:
        overall_header = ["| Turns | Hit@20 | Mean nDCG@20 |", "| ---: | ---: | ---: |"]
        overall_values = f"| {len(turns)} | {turns['hit_at_20'].mean():.3f} | {turns['ndcg@20'].mean():.3f} |"
    lines.extend([
        "## Overall",
        "",
        *overall_header,
        overall_values,
        "",
        "## Outcomes",
        "",
        "| Outcome | Turns |",
        "| --- | ---: |",
        *(f"| {outcome} | {count} |" for outcome, count in counts.items()),
        "",
        "Goal category and specificity label the whole conversation.",
        "",
    ])
    if has_top100:
        rank_21_100 = turns["ground_truth_rank"].between(21, 100).sum()
        missing_top100 = turns["ground_truth_rank"].isna().sum()
        lines.extend([
            "## Beyond top 20",
            "",
            "| Rank 21-100 | Outside top 100 |",
            "| ---: | ---: |",
            f"| {rank_21_100} | {missing_top100} |",
            "",
        ])
    for group in ("turn_number", "goal_category", "goal_specificity"):
        lines.extend([f"## By {group}", "", format_summary(turns, group), ""])

    if args.outcome == "rank_21_100":
        examples = turns[turns["ground_truth_rank"].between(21, 100)]
    elif args.outcome == "missing_top100":
        examples = turns[turns["ground_truth_rank"].isna()] if has_top100 else turns.iloc[0:0]
    else:
        examples = turns[turns["outcome"] == args.outcome]
    examples = examples.drop_duplicates("session_id").head(args.limit)
    lines.extend([f"## Examples: {args.outcome} ({len(examples)} shown)", ""])
    for _, row in examples.iterrows():
        if pd.isna(row["ground_truth_rank"]):
            rank_label = "not in top 100" if has_top100 else "not in top 20"
        else:
            rank_label = int(row["ground_truth_rank"])
        lines.extend([
            f"### {row['session_id']} — turn {row['turn_number']}",
            "",
            f"- Goal: category {row['goal_category']}, specificity {row['goal_specificity']}",
            f"- Request: {shorten(row['user_query'], width=220, placeholder='...')}",
            f"- Target: {row['ground_truth_track']}",
            *(f"- Predicted #{rank}: {track}" for rank, track in enumerate(row["predicted_top3_tracks"], start=1)),
            f"- Target rank: {rank_label}; nDCG@20: {row['ndcg@20']:.3f}",
            "",
        ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--category", help="Keep one conversation-goal category, such as G")
    parser.add_argument("--specificity", help="Keep one conversation-goal specificity, such as LH")
    parser.add_argument("--turn", type=int, help="Keep one turn number, from 1 to 8")
    parser.add_argument("--outcome", choices=OUTCOMES + DEEP_OUTCOMES, default="missing_top20")
    parser.add_argument("--limit", type=int, default=5, help="Number of example turns to show")
    args = parser.parse_args()

    if args.limit < 0:
        parser.error("--limit must be nonnegative")
    turns = load_turns(args.input)
    if args.category:
        turns = turns[turns["goal_category"] == args.category.upper()]
    if args.specificity:
        turns = turns[turns["goal_specificity"] == args.specificity.upper()]
    if args.turn is not None:
        turns = turns[turns["turn_number"] == args.turn]
    report_path = args.input.with_name(f"{args.input.stem.removesuffix('_turns')}_failure_report.md")
    report_path.write_text(format_report(turns, args), encoding="utf-8")
    print(f"Saved report to {report_path}")


if __name__ == "__main__":
    main()
