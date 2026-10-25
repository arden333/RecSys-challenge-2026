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
