# Retrieval failure analysis

Source: custom_exp03_qwen3_devset_top100_turns.jsonl

Filters: category=all, specificity=all, turn=all, outcome=missing_top20, example limit=5

## Overall

| Turns | Hit@20 | Hit@100 | Mean nDCG@20 |
| ---: | ---: | ---: | ---: |
| 8000 | 0.200 | 0.346 | 0.084 |

## Outcomes

| Outcome | Turns |
| --- | ---: |
| missing_top20 | 6402 |
| rank_11_20 | 541 |
| rank_2_10 | 876 |
| rank_1 | 181 |

Goal category and specificity label the whole conversation.

## Beyond top 20

| Rank 21-100 | Outside top 100 |
| ---: | ---: |
| 1171 | 5231 |

## By turn_number

| turn_number | Turns | Hit@20 | Hit@100 | Mean nDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1000 | 0.248 | 0.390 | 0.144 |
| 2 | 1000 | 0.246 | 0.374 | 0.119 |
| 3 | 1000 | 0.236 | 0.372 | 0.096 |
| 4 | 1000 | 0.192 | 0.363 | 0.073 |
| 5 | 1000 | 0.211 | 0.349 | 0.077 |
| 6 | 1000 | 0.181 | 0.320 | 0.064 |
| 7 | 1000 | 0.153 | 0.305 | 0.053 |
| 8 | 1000 | 0.131 | 0.296 | 0.048 |

## By goal_category

| goal_category | Turns | Hit@20 | Hit@100 | Mean nDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| A | 488 | 0.193 | 0.365 | 0.074 |
| B | 1136 | 0.178 | 0.299 | 0.070 |
| C | 464 | 0.155 | 0.274 | 0.075 |
| D | 688 | 0.167 | 0.317 | 0.079 |
| E | 760 | 0.218 | 0.359 | 0.087 |
| F | 760 | 0.292 | 0.484 | 0.132 |
| G | 616 | 0.172 | 0.287 | 0.065 |
| H | 1080 | 0.267 | 0.433 | 0.114 |
| I | 144 | 0.125 | 0.215 | 0.064 |
| J | 616 | 0.188 | 0.343 | 0.077 |
| K | 1248 | 0.159 | 0.303 | 0.067 |

## By goal_specificity

| goal_specificity | Turns | Hit@20 | Hit@100 | Mean nDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| HH | 816 | 0.353 | 0.525 | 0.179 |
| HL | 2456 | 0.215 | 0.371 | 0.088 |
| LH | 2504 | 0.206 | 0.352 | 0.086 |
| LL | 2224 | 0.120 | 0.247 | 0.044 |

## Examples: missing_top20 (5 shown)

### ba3da7b0-1e81-4d2a-90fa-65ee1f4d7348 — turn 2

- Goal: category J, specificity HH
- Request: Perfect! That was the popular song I was looking for. Now, what are some other highly popular alternative rock tracks you have?
- Target: Fluorescent Adolescent — Arctic Monkeys
- Predicted #1: Taro — alt-J
- Predicted #2: Getting Smaller — Nine Inch Nails
- Predicted #3: Get Stoned - Remastered Album Version — Hinder
- Target rank: not in top 100; nDCG@20: 0.000

### 0979c6fc-c382-4c14-be3e-2a4711fcc532 — turn 2

- Goal: category H, specificity HL
- Request: Yes, Cro-Mags is a great pick for that raw, intense 80s hardcore sound. Can you recommend a few more bands with that same kind of aggressive, no-frills energy and short song structures?
- Target: Fuck Authority — Wasted Youth
- Predicted #1: Hard Times — Cro-Mags
- Predicted #2: Amoeba — Adolescents
- Predicted #3: Subliminal — Suicidal Tendencies
- Target rank: not in top 100; nDCG@20: 0.000

### 8741b1b4-cd87-42fc-a56d-483e7f66494c — turn 1

- Goal: category H, specificity LH
- Request: I'm trying to remember an electronic band with a really powerful, almost anthemic sound.
- Target: Perpetual — VNV Nation
- Predicted #1: Electronaut — VNV Nation
- Predicted #2: Getting Away with It - 2013 Remaster; Getting Away With It - 2013 Remastered Version — Electronic
- Predicted #3: Gentlemen - Remastered; Gentlemen — The Afghan Whigs
- Target rank: not in top 100; nDCG@20: 0.000

### a510a742-18e9-4098-83a2-7e7f9a25aca7 — turn 1

- Goal: category F, specificity HL
- Request: I'm looking for some energetic electronic tracks from the late 90s and early 2000s, something good for a dance party.
- Target: One More Time — Daft Punk
- Predicted #1: Hey you what's that sound ? — Les Rythmes Digitales
- Predicted #2: Stitches — Orgy
- Predicted #3: Cloud 909 — Lone
- Target rank: not in top 100; nDCG@20: 0.000

### e17c1529-d45b-4eaf-a4dd-4e795d83c679 — turn 1

- Goal: category E, specificity HL
- Request: Start me on a journey through electronic body music, beginning with classic EBM from the early 90s, and gradually progressing towards more melodic synthpop. I'd like to steer clear of anything too harsh or industrial.
- Target: Second Voice — And One
- Predicted #1: Unbelievable — EMF
- Predicted #2: Getting Away with It - 2013 Remaster; Getting Away With It - 2013 Remastered Version — Electronic
- Predicted #3: 3 Speed — Eels
- Target rank: not in top 100; nDCG@20: 0.000
