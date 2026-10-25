# Exp01: Add `tag_list` to the BM25 track document

## Question and setup

Does adding `tag_list` to the existing track name, artist, album, and release date fields improve candidate retrieval? The baseline and Exp01 use the same public development set (8,000 turns), the full `all_tracks` catalog (47,071 tracks), the same BM25 retrieval code, response generation disabled, and the same evaluator. The only configuration change is the added `tag_list` field in `baseline-code/config/exp01_bm25_tags_devset.yaml`.

## Results

| Metric | Baseline | Exp01 | Change |
| --- | ---: | ---: | ---: |
| Hit@20 | 1,761 / 8,000 (22.01%) | 2,112 / 8,000 (26.40%) | +351 turns (+4.39 percentage points) |
| Hit@100 | 2,673 / 8,000 (33.41%) | 3,444 / 8,000 (43.05%) | +771 turns (+9.64 percentage points) |
| nDCG@20 | 0.081525 | 0.097060 | +0.015535 |
| Catalog diversity | 0.379533 | 0.454229 | +0.074696 |

The paired turn comparison shows 673 newly recovered and 322 newly lost targets in the top 20. At top 100, 993 targets were newly recovered and 222 were lost. Rank 1 remained at 77 turns in both runs. These paired counts show that the net gains coexist with regressions on individual turns.

## Remaining failures

Exp01 still misses the target in the top 20 on 5,888 turns (73.6%). Of these, 1,332 have the target at ranks 21–100 and 4,556 miss the target even at top 100. Thus candidate generation remains the main limit for those 4,556 turns; reranking only the current top 20 cannot recover them.

The generated [Exp01 failure report](custom_exp01_bm25_tags_devset_top100_failure_report.md) gives results by turn, conversation goal category, and goal specificity, plus example failures. Goal labels describe the whole conversation, not an individual turn. For example, low-low specificity improved from 15.8% to 20.5% Hit@20, while it still trails the high-high group at 37.4%. The five displayed failures are examples, not a representative sample of all failures.

## Interpretation and limits

The directional hypothesis is supported on this development set: adding tags improves both candidate inclusion metrics and nDCG@20. The controlled change includes longer documents and changed BM25 term statistics, so these results alone do not establish which tag words caused each gain. Exp01 is still a BM25-only ranking; it has no separate reranker. Response generation was off, so lexical diversity is not meaningful for this comparison. These are local public development-set results, not Blind-B leaderboard scores.

## Reproduction

Run these commands from the project root with the `recsys26` conda environment:

```bash
conda run -n recsys26 python baseline-code/custom_run_inference_devset.py --tid exp01_bm25_tags_devset --response off --top100_analysis
conda run -n recsys26 python evaluation-code/evaluate_devset.py --tid custom_exp01_bm25_tags_devset_top100
conda run -n recsys26 python evaluation-code/export_turn_analysis.py --tid custom_exp01_bm25_tags_devset_top100
conda run -n recsys26 python evaluation-code/exp/analysis/analyze_failures.py --input evaluation-code/exp/analysis/custom_exp01_bm25_tags_devset_top100_turns.jsonl
```

Baseline comparison inputs are `evaluation-code/exp/inference/devset/custom_llama1b_bm25_devset_top100.json` and `evaluation-code/exp/scores/devset/custom_llama1b_bm25_devset_top100.json`. Exp01 outputs use `custom_exp01_bm25_tags_devset_top100` in the same directories. The analysis JSONL is ignored by Git, as is the generated BM25 cache.
