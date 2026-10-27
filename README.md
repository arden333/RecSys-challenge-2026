# RecSys Challenge 2026

## Key decisions

- The baseline retrieves tracks from the previous chat history and current user query. Each track document uses `track_name`, `artist_name`, `album_name`, and `release_date`.
- This project focuses on recommendation quality, with response generation disabled. `baseline-code/custom_run_inference_devset.py` and `baseline-code/mcrs/custom_crs_baseline.py` add this option while preserving the original baseline files.
- BM25 is the main baseline because its nDCG@20 is higher than BERT's on the public development set.
- Predictions are saved for every turn. I will inspect per-turn failures to form hypotheses for later experiments.

## BM25 baseline (public development set)

Retrieval-only run with response generation disabled.

| Metric | Score |
| --- | ---: |
| nDCG@20 | 0.081525 |
| Catalog diversity | 0.379533 |
| Hit@100 | 0.334125 |

Hit@100 is a retrieval diagnostic; nDCG@20 and catalog diversity still use the top 20 predictions.

## BERT baseline (public development set)

Retrieval-only run with response generation disabled.

| Metric | Score |
| --- | ---: |
| nDCG@20 | 0.006286 |
| Catalog diversity | 0.060674 |

## Experiments

| No. | Why | Hypothesis | Variable | Result | Interpretation | Findings |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | 66.6% of targets miss BM25's top 100; name and date fields lack genre and mood terms. | Adding tags improves Hit@20 and Hit@100. | Add `tag_list` to each BM25 track document. | Hit@20: 22.01% → 26.40%; Hit@100: 33.41% → 43.05%; nDCG@20: 0.081525 → 0.097060; diversity: 0.379533 → 0.454229. | Candidate coverage improves, but some previous hits are lost; 4,556 turns still miss the top 100. | [Exp01 findings](evaluation-code/exp/analysis/exp01_bm25_tags_findings.md) |
| 02 | Assistant replies and prior track metadata may dilute the retrieval query. | With Exp01's BM25 documents unchanged, using only user messages improves later-turn Hit@20 and Hit@100. | Query uses previous and current user messages only. | vs Exp01: Hit@20 26.40% → 15.55%; Hit@100 43.05% → 28.58%; nDCG@20 0.097060 → 0.066946; diversity 0.454229 → 0.360944. | The hypothesis is rejected: all four target metrics decline and later-turn hits fall. Removing assistant text and track metadata together leaves their individual effects unknown. | [Exp02 findings](evaluation-code/exp/analysis/exp02_bm25_user_query_findings.md) |
| 03 | Exp01 BM25 misses 56.95% of targets in its top 100 and may miss semantically similar tracks with different wording. | Qwen3 embedding retrieval improves Hit@20 and Hit@100 using the same conversation input and track fields. | Replace BM25 with Qwen3-Embedding-0.6B. | vs Exp01: Hit@20 26.40% → 19.98%; Hit@100 43.05% → 34.61%; nDCG@20 0.097060 → 0.084261; diversity 0.454229 → 0.353891. | All metrics decline, so the hypothesis is rejected. Qwen3 recovers 459 BM25 top-100 misses but loses 1,134 BM25 hits; it leads only on turn 1. The effect of longer histories remains untested. | [Exp03 findings](evaluation-code/exp/analysis/exp03_qwen3_findings.md) |
