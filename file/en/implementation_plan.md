# Implementation Plan (Detailed Spec)

Based on: `file/en/data_processing.md`, `file/en/bargaining_power.md`, `deepseek_ai_prompt.md`, `file/en/fair_pay_scoring.md`, `file/en/dataset_description.md`.

This is an implementation spec you can code against directly (same pipeline, more detail than the short version). **Research conclusions are unchanged**: frequency/threshold 13.9, bargain formula, language levels, no fixed Fair Pay, etc. match the docs above.

---

## 0. Goals and boundaries

**Goal:** Run three topics once from `dataset/dataset.csv`; write results to:

| Topic | Content | Output directory |
|------|---------|------------------|
| 1 Fair Pay | EUR conversion + hourly average-rate scoring + charts & conclusions | `results/01_fair_pay/` |
| 2 Language × score | Full-sample language encoding; language vs score only on scored hourly | `results/02_language_vs_score/` |
| 3 Language × bargain | Bargain on eligible sample; language vs bargain | `results/03_language_vs_bargain/` |

**Boundaries:**

- Script style: functional modules + `main.py` orchestration; no packages, class inheritance, or config frameworks
- Empty `dataset_preparation.py`: **delete**, or fully replace its role with `main.py` (pick one; do not keep an empty shell)
- Conclusions apply only to each topic’s actual sample; do not extrapolate to the whole platform

---

## 1. Sample constraints (read before implementing)

From `file/en/dataset_description.md` (approx.; trust the live CSV):

| Item | Value |
|------|-------|
| Full table rows | ~**162** (dedupe by `id`) |
| `hourly` / `fixed` | ~**32** / **130** |
| Posting language | Mainly `en` (~120), `de` (~42) |
| Read encoding | **`utf-8-sig`** (UTF-8 with BOM) |
| Amount-related missing | Some `budget_max` missing; ~8 rows missing `bid_count` / `bid_avg` |

Implications:

- Fair Pay scores **only** on hourly → topic 2 cross-sample ceiling ~32
- Bargain on EUR-cleaned eligible rows (drop missing bid/budget and `max <= min`)
- Charts and conclusions must report **n**; do not treat a small sample as platform-wide law

---

## 2. Overall pipeline

```
dataset/dataset.csv
        │
        ▼
   [shared] read (utf-8-sig) + add_eur_columns
        │
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
 fair_pay_analysis   language_scoring   bargain_analysis
   (topic 1)           (topic 2 prep)       (topic 3)
        │                  │                  │
        │                  ▼                  │
        │         analyze_vs_fair_pay         │
        │         (topic 2, needs topic 1)    │
        │                  │                  │
        ▼                  ▼                  ▼
 results/01_…        results/02_…        results/03_…
```

**Execution order (required):**

1. Read CSV + currency conversion (once; all later steps use `*_eur` columns)
2. Fair Pay (topic 1) → `fair_pay_df`
3. Language encoding (full sample) → `lang_df`
4. Language × Fair Pay (topic 2; depends on steps 2–3)
5. Bargain + language × bargain (topic 3; depends on language columns from step 3)

---

## 3. File layout and public API

```
final_project/
├── dataset/dataset.csv
├── main.py                 # entry: call in sequence
├── currency_utils.py       # EUR conversion
├── fair_pay_analysis.py    # topic 1
├── language_scoring.py     # topic 2
├── bargain_analysis.py     # topic 3
├── requirements.txt
├── deepseek_ai_prompt.md   # prompt source (SYSTEM_PROMPT embedded in code)
├── .env                    # DEEPSEEK_API_KEY (not committed)
├── .env.example
└── results/
    ├── 01_fair_pay/
    ├── 02_language_vs_score/
    └── 03_language_vs_bargain/
```

| File | Role | Public functions |
|------|------|------------------|
| `currency_utils.py` | EUR columns | `add_eur_columns(df: pd.DataFrame) -> pd.DataFrame` |
| `fair_pay_analysis.py` | Topic 1 | `run(df: pd.DataFrame, out_dir: str \| Path) -> pd.DataFrame` |
| `language_scoring.py` | Topic 2 | `score_languages(df, out_dir) -> pd.DataFrame`; `analyze_vs_fair_pay(lang_df, fair_pay_df, out_dir) -> None` |
| `bargain_analysis.py` | Topic 3 | `run(df_with_lang: pd.DataFrame, out_dir: str \| Path) -> pd.DataFrame` |
| `main.py` | Orchestration | `main() -> None` |

Each `run` / `analyze_*` must `Path(out_dir).mkdir(parents=True, exist_ok=True)` before writing.

---

## 4. Shared: currency conversion (`currency_utils.py`)

### 4.1 Input columns

`budget_min`, `budget_max`, `bid_avg`, `currency_exchange_rate`, `currency_code`

### 4.2 Formula

`currency_exchange_rate` is relative to USD. Convert to USD then to EUR, equivalent to:

```text
amount_EUR = amount_original × rate_original / rate_EUR
```

where `rate_original` = that row’s `currency_exchange_rate`, `rate_EUR` = the EUR row’s rate.

### 4.3 Algorithm

```python
def add_eur_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    eur_rates = out.loc[out["currency_code"] == "EUR", "currency_exchange_rate"].dropna()
    # mode; if mode unavailable, first non-null
    rate_eur = eur_rates.mode().iloc[0]
    rate_row = out["currency_exchange_rate"]
    for col in ("budget_min", "budget_max", "bid_avg"):
        out[f"{col}_eur"] = out[col] * rate_row / rate_eur
        # original NaN → corresponding *_eur stays NaN (pandas multiply propagates)
    return out
```

### 4.4 Output columns

| New column | Meaning |
|------------|---------|
| `budget_min_eur` | Budget floor (EUR) |
| `budget_max_eur` | Budget ceiling (EUR) |
| `bid_avg_eur` | Average bid (EUR) |

### 4.5 Hard rules

- Later Fair Pay / bargain **must not** use unconverted `budget_*` / `bid_avg` for amounts
- `rate_EUR` must resolve; if no EUR row exists, `raise ValueError` and prompt to check data

---

## 5. Topic 1: `fair_pay_analysis.py`

Threshold from `file/en/fair_pay_scoring.md`: German minimum wage **13.90 EUR/hour**; this project awards 0/1 by whether average hourly rate `>= 13.9`.

### 5.1 Sample funnel

```text
Full table (~162)
  → type == "hourly"                    (~32)
  → both budget_min_eur and budget_max_eur non-null
  → analysis sample fair_pay_df
```

- **Do not** Fair Pay score fixed jobs
- Missing either EUR budget column → drop

### 5.2 Derived columns and score

```python
hourly_min_eur = budget_min_eur
hourly_max_eur = budget_max_eur
hourly_avg_eur = (hourly_min_eur + hourly_max_eur) / 2
fair_pay_score = 1 if hourly_avg_eur >= 13.9 else 0   # vectorized: (avg >= 13.9).astype(int)
```

Suggested constant: `FAIR_PAY_THRESHOLD_EUR = 13.9`.

### 5.3 Export CSV: `results/01_fair_pay/fair_pay_hourly.csv`

Suggested columns (this order is fine):

| Column | Notes |
|--------|-------|
| `id` | Project ID |
| `title` | Title |
| `type` | Should be `hourly` |
| `job_category_names` | Category (raw string) |
| `currency_code` | Original currency (traceability) |
| `budget_min_eur` | |
| `budget_max_eur` | |
| `hourly_min_eur` | Same as min |
| `hourly_avg_eur` | |
| `hourly_max_eur` | |
| `fair_pay_score` | 0 or 1 |
| `url` | Optional, for spot checks |

### 5.4 Required charts (3)

| File | Content | Drawing rules |
|------|---------|---------------|
| `score_distribution.png` | Score 0/1 counts | Bar chart; x=`fair_pay_score`, y=count; title includes n |
| `pass_rate_by_category.png` | Pass rate by category | See category merge below; x=category, y=pass rate (0–1 or %) |
| `hourly_avg_boxplot.png` | Average hourly boxplot | Group by `fair_pay_score`; optional horizontal reference at y=13.9 |

**Category merge rules:**

- Group by raw `job_category_names` string (multi-label joined strings count as one class; do not split)
- If a class has **n < 3**, merge into label `Other`
- Show n per class in legend or annotations

### 5.5 `结论.md` / conclusions template

```markdown
# Fair Pay Analysis Conclusions

- Analysis sample size n = …
- Pass count (score=1) = …, pass rate = …
- Average hourly (`hourly_avg_eur`) median / mean = …
- Threshold = 13.9 EUR/h

## By category (brief)
- …

## Limitations
- Hourly only; no fixed estimate; work-related costs not deducted; small n; descriptive of this sample only.
```

### 5.6 Function signature

```python
def run(df: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    """Input must already have *_eur. Write csv/charts/conclusions, return fair_pay_df (for topic 2)."""
```

---

## 6. Topic 2: `language_scoring.py`

### 6.1 Encoding definition

| Field | Values | Meaning |
|-------|--------|---------|
| `de_level` | 0–3 | 0=not required; 1=A1/A2; 2=B1/B2; 3=C1/C2 |
| `en_level` | 1–3 | 1=A1/A2; 2=B1/B2; 3=C1/C2 (**no 0**: default at least beginner) |
| `de_reason` / `en_reason` | string | Short rationale (must be bilingual CN/EN; AI results prefix `[AI辅助]`) |

Write these four columns for **all** jobs.

### 6.2 Decision pipeline (strict priority)

For each row, scan text from: `job_names`, `title`, `description` (may concatenate into one case-insensitive search string; note hit source in reason).

```text
1. Rule layer (CEFR regex + skill tags + phrase lexicon)
      → multiple hits same language: take min(level)
      → reason prefix [rule], format "中文 / English"
2. If both de_level and en_level are set → stop
3. Else (including soft defaults like "no German requirement" / "default English beginner") → call AI/DeepSeek
      → fill missing; reason prefix [AI辅助]; reasons must be bilingual
4. Posting-language floor (forced after AI / rules):
      language == "en" → en_level = max(en_level, 1)
      language == "de" → de_level = max(de_level, 1)
5. If still missing (no key / API failure) → fallback:
      missing de → de_level=0, de_reason="[fallback] 中文 / English"
      missing en → en_level=1, en_reason="[fallback] 中文 / English"
      and logging.warning
```

**Forbidden:** rule layer alone ending with `[rule] no German requirement found` or `[rule] default English beginner` — those cases must go through **AI assist**.

“Complete” means: both `de_level` and `en_level` are non-null valid integers.

### 6.3 Rule-layer details

#### (A) CEFR regex (examples)

Near German/English context, or match globally then assign by language keywords:

- Pattern example: `(?i)\b(A1|A2|B1|B2|C1|C2)\b`
- Map: A1/A2→1, B1/B2→2, C1/C2→3
- If CEFR sits next to `German` / `Deutsch` / `德语` → `de`; `English` / `Englisch` / `英语` → `en`
- If language cannot be assigned: ignore that CEFR hit (later rules or DeepSeek), avoid mislabeling

#### (B) Skill tags

In `job_names` (case-insensitive, light normalization OK):

| Tag example | Language | Default level (no finer modifier) |
|-------------|----------|-----------------------------------|
| German / Deutsch | de | 2 (fluent); if same row has CEFR/phrases, then take min |
| English / Englisch | en | 2 |

Language name only, no degree word → use table default; if degree words appear in the same field, prefer phrase lexicon and take min.

#### (C) Phrase lexicon (in-script dict, lowercase keys)

At least cover (extend synonyms as needed):

| phrase (lowercase) | Language | level |
|--------------------|----------|-------|
| `no german` / `german not required` / `nicht erforderlich` (with german context) | de | 0 |
| `basic german` / `einfaches deutsch` / `a1`/`a2` + german | de | 1 |
| `fluent german` / `gutes deutsch` / `b1`/`b2` + german | de | 2 |
| `native german` / `muttersprachler` / `c1`/`c2` + german / `verhandlungssicher` | de | 3 |
| `basic english` / `einfaches englisch` | en | 1 |
| `fluent english` / `gutes englisch` | en | 2 |
| `native english` / `muttersprachliches englisch` / `business english` (if high, 2 or 3; prefer 2 when unsure) | en | 2 or 3 |

Match: substring search on `(title + " " + job_names + " " + description).lower()`; multiple hits same language → **`min(levels)`**.

### 6.4 DeepSeek call

Full prompt: `deepseek_ai_prompt.md`. Implementation notes:

```python
from openai import OpenAI
from dotenv import load_dotenv
import os, json, logging

load_dotenv()  # project-root .env

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# messages: system = SYSTEM_PROMPT; user = id/title/language/job_names/...
# model = "deepseek-v4-pro"
# parse response.choices[0].message.content as JSON
# validate de_level in {0,1,2,3}, en_level in {1,2,3}
# when writing reason: f"[AI辅助] {reason}" (reason must be bilingual: "中文 / English")
```

- Call **when** rules cannot complete de/en (including “no German requirement” / “default English beginner”); do not skip AI with pure-rule soft defaults
- No `DEEPSEEK_API_KEY` or request error: do not abort the pipeline; use step-5 fallback and `logging.warning`

### 6.5 Intermediate table: `results/02_language_vs_score/language_all.csv`

Suggested columns:

| Column | Notes |
|--------|-------|
| `id` | |
| `title` | |
| `language` | Posting language |
| `type` | |
| `job_names` | |
| `job_category_names` | |
| `de_level` | |
| `en_level` | |
| `de_reason` | |
| `en_reason` | |
| `url` | Optional |

`score_languages` return value `lang_df` must at least include the language columns + `id` (may append on a full-table copy).

### 6.6 Language × Fair Pay

| Item | Rule |
|------|------|
| Sample | `fair_pay_df` **inner merge** `lang_df` on `id` |
| Cross-tabs | For `de_level` / `en_level` separately: n, mean score, pass rate |
| Optional saves | `cross_de.csv` / `cross_en.csv` |

**Required charts:**

- `de_level_vs_pass_rate.png` — x=`de_level`, y=pass rate; annotate n on/near bars
- `en_level_vs_pass_rate.png` — same

**Conclusions template:**

```markdown
# Language × Fair Pay Conclusions

- Cross-sample n = … (scored hourly only)
- German levels: n / pass rate …
- English levels: n / pass rate …
- Observations (descriptive, no causal claims) …
- Limitations: small n; language = job requirement encoding, not workers’ actual ability.
```

### 6.7 Function signatures

```python
def score_languages(df: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    """Encode full sample; write language_all.csv; return table with language columns."""

def analyze_vs_fair_pay(
    lang_df: pd.DataFrame,
    fair_pay_df: pd.DataFrame,
    out_dir: str | Path,
) -> None:
    """Merge, cross-stats + charts + conclusions."""
```

---

## 7. Topic 3: `bargain_analysis.py`

Definitions and formulas fully per `file/en/bargaining_power.md`; amounts always use EUR columns.

### 7.1 Sample cleaning

Drop rows meeting any of:

- Missing `bid_count` / `bid_avg_eur` / `budget_min_eur` / `budget_max_eur`
- `budget_max_eur <= budget_min_eur`

Input must already include topic-2 `de_level` / `en_level` (`main` passes `lang_df`).

### 7.2 Indicators and composite

\[
P_i = \frac{bid\_avg\_eur_i - budget\_min\_eur_i}{budget\_max\_eur_i - budget\_min\_eur_i},
\quad
C_i = \log(1 + bid\_count_i)
\]

Z-score on the **full cleaned sample** (`ddof=0`):

\[
z(P_i)=\frac{P_i-\bar P}{s_P},\quad
z(C_i)=\frac{C_i-\bar C}{s_C}
\]

\[
bargain\_score_i = 0.5 \cdot z(P_i) - 0.5 \cdot z(C_i)
\]

(i.e. \(\alpha = 0.5\).)

### 7.3 Discrete tiers (required)

By `bargain_score` quantiles:

| `bargain_tier` | Rule |
|----------------|------|
| `low` | ≤ Q1 |
| `mid` | Q1–Q3 (boundary assignment consistent via `pandas.qcut` or explicit quantiles) |
| `high` | ≥ Q3 |

Useful for crossing with language levels.

### 7.4 fixed / hourly note (must appear in conclusions)

- This implementation: **one z-score on fixed + hourly together** (aligned with bargain doc sketch)
- Limitation: `bid_avg` / budget mean different things by type (total vs hourly); \(P\) as relative interval position is still computable, but in conclusions report means by `type` or note “not standardized separately by type”

### 7.5 Implementation sketch

```python
import numpy as np

sub = df.dropna(subset=["bid_count", "bid_avg_eur", "budget_min_eur", "budget_max_eur"]).copy()
sub = sub[sub["budget_max_eur"] > sub["budget_min_eur"]]

sub["P"] = (sub["bid_avg_eur"] - sub["budget_min_eur"]) / (
    sub["budget_max_eur"] - sub["budget_min_eur"]
)
sub["C"] = np.log1p(sub["bid_count"])
sub["z_P"] = (sub["P"] - sub["P"].mean()) / sub["P"].std(ddof=0)
sub["z_C"] = (sub["C"] - sub["C"].mean()) / sub["C"].std(ddof=0)
alpha = 0.5
sub["bargain_score"] = alpha * sub["z_P"] - (1 - alpha) * sub["z_C"]
# bargain_tier: cut low/mid/high at Q1/Q3
```

### 7.6 Outputs (`results/03_language_vs_bargain/`)

**`bargain_scored.csv` suggested columns:**

`id`, `title`, `type`, `de_level`, `en_level`, `de_reason`, `en_reason`, `bid_count`, `budget_min_eur`, `budget_max_eur`, `bid_avg_eur`, `P`, `C`, `z_P`, `z_C`, `bargain_score`, `bargain_tier`, `url`(optional)

**Charts:**

| File | Content |
|------|---------|
| `bargain_score_hist.png` | Histogram of `bargain_score` |
| `de_level_vs_bargain.png` | German level × bargain (boxplot or mean bar + error) |
| `en_level_vs_bargain.png` | English level × bargain (same) |

Optional: `tier_by_de_level.png` (stacked proportions).

**Conclusions template:**

```markdown
# Language × Bargain Conclusions

- Bargain-eligible sample n = …
- bargain_score: mean / median / quantiles …
- Mean bargain by de_level / en_level …
- Brief by type (fixed vs hourly) …
- Limitations: project-level proxy; no award price; fixed/hourly jointly standardized …
```

### 7.7 Function signature

```python
def run(df_with_lang: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    """Clean → compute bargain → language cross charts/conclusions; return bargain_scored table."""
```

---

## 8. Entry: `main.py`

```python
def main() -> None:
    # 1. df = pd.read_csv("dataset/dataset.csv", encoding="utf-8-sig")
    # 2. df = add_eur_columns(df)
    # 3. fair_df = fair_pay_analysis.run(df, "results/01_fair_pay")
    # 4. lang_df = language_scoring.score_languages(df, "results/02_language_vs_score")
    # 5. language_scoring.analyze_vs_fair_pay(lang_df, fair_df, "results/02_language_vs_score")
    # 6. bargain_analysis.run(lang_df, "results/03_language_vs_bargain")

if __name__ == "__main__":
    main()
```

Run (project root, venv activated):

```bash
python main.py
```

---

## 9. Dependencies and environment

### 9.1 `requirements.txt` (suggested)

```text
pandas
numpy
matplotlib
openai
python-dotenv
```

(If `pandas` already present, add the rest; charts use `matplotlib`, `seaborn` not required.)

### 9.2 Environment variables

| Variable | Notes |
|----------|-------|
| `DEEPSEEK_API_KEY` | DeepSeek API key; see `.env.example` |

- Do not commit `.env` (already in `.gitignore`)
- Without a key, language module uses fallback; **the full pipeline must still complete**

### 9.3 DeepSeek call strategy

Call only when rules cannot complete de/en, to control call count and cost.

---

## 10. Out of scope

- No Fair Pay for fixed via hour estimation
- No complex OOP / plugins / config frameworks
- No interactive dashboard
- Do not extrapolate conclusions to the whole platform; do not treat language requirements as workers’ true ability
- Do not commit `.env` or real API keys

---

## 11. Acceptance checklist

### Shared

- [ ] `budget_min_eur` / `budget_max_eur` / `bid_avg_eur` exist and formula is correct
- [ ] Later amount analyses do not misuse unconverted columns
- [ ] CSV read with `utf-8-sig`

### Topic 1 — `results/01_fair_pay/`

- [ ] `fair_pay_hourly.csv`: hourly only; three hourly columns + `fair_pay_score`
- [ ] Score only from `hourly_avg_eur >= 13.9`
- [ ] Three required charts + conclusions (with n, pass rate)

### Topic 2 — `results/02_language_vs_score/`

- [ ] `language_all.csv`: full sample; `de_level` 0–3, `en_level` 1–3; reason columns
- [ ] Rules first; AI reasons use `[AI辅助]` and bilingual CN/EN; failures use `[fallback]` (bilingual)
- [ ] No pure-rule endings of `no German requirement found` / `default English beginner`
- [ ] Posting-language floor applied
- [ ] Cross charts (de/en × pass rate) + conclusions

### Topic 3 — `results/03_language_vs_bargain/`

- [ ] `bargain_scored.csv`: P, C, z, `bargain_score`, `bargain_tier`
- [ ] Cleaning, α=0.5, `ddof=0` match spec
- [ ] Distribution chart + language × bargain charts + conclusions (mention fixed/hourly limitation)

### End-to-end

- [ ] `python main.py` runs through once
- [ ] Without `DEEPSEEK_API_KEY`, still completes and writes all directory artifacts (language gaps → fallback)
