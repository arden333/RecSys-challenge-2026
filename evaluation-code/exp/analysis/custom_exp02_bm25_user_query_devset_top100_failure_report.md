# Retrieval failure analysis

Source: custom_exp02_bm25_user_query_devset_top100_turns.jsonl

Filters: category=all, specificity=all, turn=all, outcome=missing_top20, example limit=5

## Overall

| Turns | Hit@20 | Hit@100 | Mean nDCG@20 |
| ---: | ---: | ---: | ---: |
| 8000 | 0.155 | 0.286 | 0.067 |

## Outcomes

| Outcome | Turns |
| --- | ---: |
| missing_top20 | 6756 |
| rank_11_20 | 410 |
| rank_2_10 | 690 |
| rank_1 | 144 |

Goal category and specificity label the whole conversation.

## Beyond top 20

| Rank 21-100 | Outside top 100 |
| ---: | ---: |
| 1042 | 5714 |

## By turn_number

| turn_number | Turns | Hit@20 | Hit@100 | Mean nDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1000 | 0.227 | 0.335 | 0.133 |
| 2 | 1000 | 0.205 | 0.360 | 0.098 |
| 3 | 1000 | 0.171 | 0.305 | 0.066 |
| 4 | 1000 | 0.160 | 0.284 | 0.058 |
| 5 | 1000 | 0.140 | 0.261 | 0.055 |
| 6 | 1000 | 0.128 | 0.253 | 0.045 |
| 7 | 1000 | 0.116 | 0.251 | 0.046 |
| 8 | 1000 | 0.097 | 0.237 | 0.035 |

## By goal_category

| goal_category | Turns | Hit@20 | Hit@100 | Mean nDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| A | 488 | 0.125 | 0.279 | 0.047 |
| B | 1136 | 0.125 | 0.243 | 0.052 |
| C | 464 | 0.136 | 0.239 | 0.062 |
| D | 688 | 0.112 | 0.228 | 0.055 |
| E | 760 | 0.103 | 0.192 | 0.048 |
| F | 760 | 0.254 | 0.418 | 0.111 |
| G | 616 | 0.117 | 0.200 | 0.051 |
| H | 1080 | 0.247 | 0.414 | 0.104 |
| I | 144 | 0.132 | 0.153 | 0.067 |
| J | 616 | 0.141 | 0.338 | 0.059 |
| K | 1248 | 0.148 | 0.274 | 0.061 |

## By goal_specificity

| goal_specificity | Turns | Hit@20 | Hit@100 | Mean nDCG@20 |
| --- | ---: | ---: | ---: | ---: |
| HH | 816 | 0.282 | 0.462 | 0.150 |
| HL | 2456 | 0.183 | 0.338 | 0.076 |
| LH | 2504 | 0.159 | 0.274 | 0.065 |
| LL | 2224 | 0.076 | 0.177 | 0.029 |

## Examples: missing_top20 (5 shown)

### ba3da7b0-1e81-4d2a-90fa-65ee1f4d7348 — turn 2

- Goal: category J, specificity HH
- Request: Perfect! That was the popular song I was looking for. Now, what are some other highly popular alternative rock tracks you have?
- Target: Fluorescent Adolescent — Arctic Monkeys
- Predicted #1: Heart-Shaped Box — Nirvana
- Predicted #2: Heart-Shaped Box — Dead Sara
- Predicted #3: Doomed User — Deftones
- Target rank: not in top 100; nDCG@20: 0.000

### 0979c6fc-c382-4c14-be3e-2a4711fcc532 — turn 1

- Goal: category H, specificity HL
- Request: I'm looking for 80s American hardcore punk bands known for their raw energy and short, intense songs.
- Target: Hard Times — Cro-Mags
- Predicted #1: King of the Hill — Minutemen
- Predicted #2: Room 13 — Black Flag
- Predicted #3: K05-0564 — Kid Dynamite
- Target rank: not in top 100; nDCG@20: 0.000

### 8741b1b4-cd87-42fc-a56d-483e7f66494c — turn 1

- Goal: category H, specificity LH
- Request: I'm trying to remember an electronic band with a really powerful, almost anthemic sound.
- Target: Perpetual — VNV Nation
- Predicted #1: Deadhead — Devin Townsend Band
- Predicted #2: One Man Drinking Games — Mayday Parade
- Predicted #3: Almost Easy — Avenged Sevenfold
- Target rank: not in top 100; nDCG@20: 0.000

### a510a742-18e9-4098-83a2-7e7f9a25aca7 — turn 1

- Goal: category F, specificity HL
- Request: I'm looking for some energetic electronic tracks from the late 90s and early 2000s, something good for a dance party.
- Target: One More Time — Daft Punk
- Predicted #1: Close to the source — LTJ Bukem
- Predicted #2: Human After All — Daft Punk
- Predicted #3: Jump — Madonna
- Target rank: 89; nDCG@20: 0.000

### e17c1529-d45b-4eaf-a4dd-4e795d83c679 — turn 1

- Goal: category E, specificity HL
- Request: Start me on a journey through electronic body music, beginning with classic EBM from the early 90s, and gradually progressing towards more melodic synthpop. I'd like to steer clear of anything too harsh or industrial.
- Target: Second Voice — And One
- Predicted #1: Spit It Out — Aesthetic Perfection
- Predicted #2: The Source — God Module
- Predicted #3: Harsh Generation — Grendel
- Target rank: 66; nDCG@20: 0.000
