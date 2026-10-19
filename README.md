# RecSys Challenge 2026

## Key decisions

- The baseline retrieves tracks from the previous chat history and current user query. Each track document uses `track_name`, `artist_name`, `album_name`, and `release_date`.
- This project focuses on recommendation quality, with response generation disabled. `baseline-code/custom_run_inference_devset.py` and `baseline-code/mcrs/custom_crs_baseline.py` add this option while preserving the original baseline files.
- Predictions are saved for every turn. I will inspect per-turn failures to form hypotheses for later experiments.

## BM25 baseline (public development set)

Retrieval-only run with response generation disabled.

| Metric | Score |
| --- | ---: |
| nDCG@20 | 0.081525 |
| Catalog diversity | 0.379533 |
