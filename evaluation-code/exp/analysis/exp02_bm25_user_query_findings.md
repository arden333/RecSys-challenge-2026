# Exp02: Use only user messages as the BM25 query

## Question and setup

Does removing prior assistant replies and recommended-track metadata from the retrieval query improve candidate retrieval? Exp02 keeps the Exp01 `tag_list` track document, BM25 index, full `all_tracks` catalog (47,071 tracks), public development set (8,000 turns), and evaluator. It changes only the retrieval query: all previous user messages plus the current user request are joined in chronological order. Response generation remains off. The Exp02 YAML is byte-for-byte identical to the Exp01 YAML; its name separates output files.

## Results

| Metric | Original BM25 | Exp01: tags | Exp02: user messages only |
| --- | ---: | ---: | ---: |
| Hit@20 | 1,761 / 8,000 (22.01%) | 2,112 / 8,000 (26.40%) | 1,244 / 8,000 (15.55%) |
| Hit@100 | 2,673 / 8,000 (33.41%) | 3,444 / 8,000 (43.05%) | 2,286 / 8,000 (28.58%) |
| nDCG@1 | 0.009625 | 0.009625 | 0.018000 |
| nDCG@20 | 0.081525 | 0.097060 | 0.066946 |
| Catalog diversity | 0.379533 | 0.454229 | 0.360944 |

Relative to Exp01, Exp02 loses 868 top-20 hits, 1,158 top-100 hits, and 0.030114 nDCG@20. The first-turn top-100 lists are identical across the two runs for all 1,000 sessions, as expected because no earlier messages exist at turn 1.

## Paired changes

| Exp01 target rank | Exp02 top 20 | Exp02 ranks 21–100 | Exp02 outside top 100 |
| --- | ---: | ---: | ---: |
| Top 20 | 1,082 | 431 | 599 |
| Ranks 21–100 | 132 | 482 | 718 |
| Outside top 100 | 30 | 129 | 4,397 |

At top 20, 162 turns become hits while 1,030 former hits are lost. At top 100, 159 turns become hits while 1,317 former hits are lost. The losses substantially exceed the gains.

Two concrete examples illustrate both directions. For session `f4212c3e-1e25-469c-affc-cdf949744cae`, turn 3 asks for an ocean-themed orchestral piece after earlier recommendations; the target, *The Ocean Chose You*, moves from rank 4 in Exp01 to outside the top 100 in Exp02. For session `8bee6f03-8cae-44ae-9325-455dc1138549`, turn 4 asks for music in the style of Marcos Valle; the target, *A Paraíba Não é Chicago*, moves from outside the top 100 to rank 3. These examples show ranking changes, not why the changes happened.

| Turn | Exp01 Hit@20 | Exp02 Hit@20 | Exp01 Hit@100 | Exp02 Hit@100 |
| --- | ---: | ---: | ---: | ---: |
| 1 | 227 / 1,000 | 227 / 1,000 | 335 / 1,000 | 335 / 1,000 |
| 2 | 341 / 1,000 | 205 / 1,000 | 506 / 1,000 | 360 / 1,000 |
| 3 | 300 / 1,000 | 171 / 1,000 | 487 / 1,000 | 305 / 1,000 |
| 4 | 277 / 1,000 | 160 / 1,000 | 456 / 1,000 | 284 / 1,000 |
| 5 | 248 / 1,000 | 140 / 1,000 | 415 / 1,000 | 261 / 1,000 |
| 6 | 253 / 1,000 | 128 / 1,000 | 424 / 1,000 | 253 / 1,000 |
| 7 | 243 / 1,000 | 116 / 1,000 | 419 / 1,000 | 251 / 1,000 |
| 8 | 223 / 1,000 | 97 / 1,000 | 402 / 1,000 | 237 / 1,000 |

## Remaining failures and interpretation

Exp02 misses the target in the top 20 on 6,756 turns. Of these, 1,042 have the target at ranks 21–100 and 5,714 miss it even at top 100. The generated [Exp02 failure report](custom_exp02_bm25_user_query_devset_top100_failure_report.md) includes breakdowns by turn, conversation goal category, and specificity, plus example failures. Goal labels apply to the whole conversation, not to an individual turn.

The directional hypothesis is rejected on this development set. Removing non-user history harms retrieval overall, even though nDCG@1 improves. Prior assistant text and recommended-track metadata were removed together, so this experiment cannot identify which source of context was useful. The unchanged first-turn predictions support that the observed difference comes from historical messages, but they do not explain the mechanism. A single annotated target per turn also means a miss does not prove that every recommended track is unsuitable.

These are local public development-set results, not Blind-B leaderboard scores. Response generation was off, so lexical diversity is not meaningful here.

## Reproduction

Run these commands from the project root using the `recsys26` environment:

```bash
conda run -n recsys26 python baseline-code/custom_run_inference_devset.py --tid exp02_bm25_user_query_devset --response off --top100_analysis
conda run -n recsys26 python evaluation-code/evaluate_devset.py --tid custom_exp02_bm25_user_query_devset_top100
conda run -n recsys26 python evaluation-code/export_turn_analysis.py --tid custom_exp02_bm25_user_query_devset_top100
conda run -n recsys26 python evaluation-code/exp/analysis/analyze_failures.py --input evaluation-code/exp/analysis/custom_exp02_bm25_user_query_devset_top100_turns.jsonl
```

The Exp01 and Exp02 prediction and score JSON files are stored in matching `evaluation-code/exp/inference/devset` and `evaluation-code/exp/scores/devset` locations. The turn-level JSONL and BM25 cache are ignored by Git. The `baseline-code/mcrs/custom_crs_baseline.py` implementation at the Exp02 checkpoint constructs user-message-only queries; to reproduce Exp01, use its earlier committed implementation.
