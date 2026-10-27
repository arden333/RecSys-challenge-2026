# Exp03: Qwen3 dense retrieval with full conversation context

## Question and setup

Can Qwen3-Embedding-0.6B recover relevant tracks that the Exp01 BM25 retriever misses, when both search the same complete catalog and use the same conversation history and track fields? The comparison uses all 8,000 turns of the public development set and the 47,071-track `all_tracks` catalog. Response generation is disabled. No reranker is used.

The retrieval query contains the current user request and all preceding user, assistant, and recommended-track metadata messages. Track documents contain `track_name`, `artist_name`, `album_name`, `release_date`, and `tag_list`. Qwen3 receives the fixed query instruction: "Retrieve music tracks matching the user's current request and conversation context." The model produces normalized dense vectors, and tracks are ranked by their dot product with the query vector.

The Qwen3 tokenizer audit found a maximum of 4,923 tokens among the complete development queries and 893 tokens among catalog documents. The configured limit is 4,923 tokens, below the model's 32,768-token input limit. The retriever rejects inputs above the configured limit instead of truncating them. Inference uses the Mac's MPS device.

## Results

| Metric | Exp01 BM25 | Exp03 Qwen3 | Qwen3 change |
| --- | ---: | ---: | ---: |
| Hit@20 | 2,112 / 8,000 (26.40%) | 1,598 / 8,000 (19.98%) | -514 turns (-6.43 percentage points) |
| Hit@100 | 3,444 / 8,000 (43.05%) | 2,769 / 8,000 (34.61%) | -675 turns (-8.44 percentage points) |
| nDCG@20 | 0.097060 | 0.084261 | -0.012799 |
| Catalog diversity | 0.454229 | 0.353891 | -0.100338 |

Both retrievers were evaluated on the same 8,000 development turns with the official local evaluator. The Qwen3 result does not support replacing Exp01 BM25 with this dense retriever alone. Qwen3 did place the target first on 181 turns versus 77 for BM25, but it missed substantially more targets at ranks 20 and 100.

### Hit rates by conversation turn

Each turn number has 1,000 development cases. Each cell shows the number of exact target hits and the corresponding hit rate.

| Turn | BM25 Hit@20 | Qwen3 Hit@20 | BM25 Hit@100 | Qwen3 Hit@100 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 227 (22.7%) | 248 (24.8%) | 335 (33.5%) | 390 (39.0%) |
| 2 | 341 (34.1%) | 246 (24.6%) | 506 (50.6%) | 374 (37.4%) |
| 3 | 300 (30.0%) | 236 (23.6%) | 487 (48.7%) | 372 (37.2%) |
| 4 | 277 (27.7%) | 192 (19.2%) | 456 (45.6%) | 363 (36.3%) |
| 5 | 248 (24.8%) | 211 (21.1%) | 415 (41.5%) | 349 (34.9%) |
| 6 | 253 (25.3%) | 181 (18.1%) | 424 (42.4%) | 320 (32.0%) |
| 7 | 243 (24.3%) | 153 (15.3%) | 419 (41.9%) | 305 (30.5%) |
| 8 | 223 (22.3%) | 131 (13.1%) | 402 (40.2%) | 296 (29.6%) |

## Paired turn comparison

| Cutoff | Both hit | BM25 only | Qwen3 only | Both miss |
| --- | ---: | ---: | ---: | ---: |
| Top 20 | 1,178 | 934 | 420 | 5,468 |
| Top 100 | 2,310 | 1,134 | 459 | 4,097 |

Qwen3 recovered 459 of the 4,556 targets that BM25 missed at top 100 (10.1% of those misses), but lost 1,134 targets that BM25 found. The top-100 union contains the target on 3,903 turns (48.79%); the top-20 union does so on 2,532 turns (31.65%). These are oracle coverage counts from two separate lists, not measured results of a merged top-100 or top-20 retriever.

Qwen3 was stronger only on the first turn: Hit@20 was 248/1,000 versus 227/1,000 for BM25, and Hit@100 was 390/1,000 versus 335/1,000. BM25 was stronger at both cutoffs on every later turn. By turn 8, Hit@20 was 131/1,000 for Qwen3 versus 223/1,000 for BM25; Hit@100 was 296/1,000 versus 402/1,000. Qwen3's decline across turns is consistent with difficulty using longer histories, but this experiment does not isolate history length as the cause. Across the four conversation-goal specificity groups and all 11 goal categories, BM25 also had higher Hit@20 and Hit@100.

The [Qwen3 failure report](custom_exp03_qwen3_devset_top100_failure_report.md) records 1,171 targets at ranks 21-100 and 5,231 outside the top 100. The five displayed failures are examples, not a representative sample of all failures.

## Interpretation and limits

The directional replacement hypothesis is not supported: Qwen3 alone underperformed Exp01 BM25 on Hit@20, Hit@100, nDCG@20, and catalog diversity. The 459 Qwen3-only top-100 hits establish some complementary coverage, but a combined retriever needs its own fixed-size ranking and evaluation before any improvement claim. The model, query instruction, representation, and scoring method all differ from BM25, so these results do not identify one cause of the gap.

This is a local public development-set experiment, not a Blind-B leaderboard result. User profiles are not included in the retrieval query by the current baseline pipeline. No response quality is assessed because response generation is disabled.

## Reproduction

Run these commands from the project root in the `recsys26` conda environment. The first retrieval run downloads the public Qwen3 model if its weights are not cached. `--resume` writes a per-turn checkpoint during the full run and removes it after the final prediction JSON is saved.

```bash
conda run -n recsys26 python baseline-code/exp03_token_audit.py --model qwen3
conda run -n recsys26 python baseline-code/custom_run_inference_devset.py --tid exp03_qwen3_devset --response off --top100_analysis --batch_size 1 --resume
conda run -n recsys26 python evaluation-code/evaluate_devset.py --tid custom_exp03_qwen3_devset_top100
conda run -n recsys26 python evaluation-code/export_turn_analysis.py --tid custom_exp03_qwen3_devset_top100
conda run -n recsys26 python evaluation-code/exp/analysis/analyze_failures.py --input evaluation-code/exp/analysis/custom_exp03_qwen3_devset_top100_turns.jsonl
conda run -n recsys26 python evaluation-code/exp/analysis/compare_exp03_retrievers.py
```

The final predictions are saved at `evaluation-code/exp/inference/devset/custom_exp03_qwen3_devset_top100.json`. The official local evaluator writes `evaluation-code/exp/scores/devset/custom_exp03_qwen3_devset_top100.json`. The paired comparison writes `evaluation-code/exp/analysis/exp03_paired_turns.jsonl` with the BM25 and Qwen3 top-20 and top-100 lists, target ranks, and turn-level metrics.
