# Data Processing

The scripts process `dataset.csv` as follows:

1. Convert all wage/amount columns to euros.
2. Among `hourly` jobs, drop rows with missing hourly budget fields; compute minimum hourly rate, average hourly rate `((min + max) / 2)`, and maximum hourly rate; score on **average hourly rate** (0 or 1: whether ≥ 13.9 EUR/hour). Produce charts and short conclusions using `job_category_names` (or similar). Save CSVs/images under the matching `results/` topic folder.
3. Define German levels: required good German C1/C2; fluent German B1/B2; basic German A1/A2; German not required; and English levels: A1/A2 beginner, B1/B2 fluent, C1/C2 proficient. Encode all jobs → German level (0,1,2,3), English level (1,2,3), plus reason columns for EN/DE.
4. Coding rules: see “Language encoding rules” below.
5. Among hourly jobs that already have a Fair Pay score, study the relationship between English/German level and the job score.
6. Define bargaining level using `file/en/bargaining_power.md` (computed on bargain-eligible jobs).

---

## Notes (execution conventions — unambiguous)

### Three research topics and directories (aligned with readme)

| Topic | Content | Output directory |
|------|---------|------------------|
| 1 Fair Pay | EUR conversion + hourly average-rate scoring + charts & conclusions | `results/01_fair_pay/` |
| 2 Language × score | Full-sample language encoding; language vs score only on scored hourly jobs | `results/02_language_vs_score/` |
| 3 Language × bargain | Compute bargain on eligible sample; analyze language vs bargain | `results/03_language_vs_bargain/` |

Implementation: 3 analysis scripts + 1 main entry; charts with matplotlib (or seaborn); save images in the matching folder; write conclusions as md/txt in the same folder.

### 1. Currency conversion (all amount columns, full sample)

- Formula: `amount_EUR = amount_original × rate_original / rate_EUR`  
  (`currency_exchange_rate` is relative to USD: convert to USD then to EUR)
- Columns to convert: all amount columns, at least `budget_min`, `budget_max`, `bid_avg`
- Fair Pay and bargain analyses both use EUR amounts (bargain relative position also uses the same-currency interval after conversion)

### 2. Fair Pay scoring (hourly only)

- **Do not** score Fair Pay for `fixed` jobs
- Drop rule: in hourly rows, if either `budget_min` or `budget_max` is missing → drop (also drop if other required fields are missing at analysis time)
- Derived: `hourly_min_eur`, `hourly_avg_eur = (min+max)/2`, `hourly_max_eur`
- **One score column only:** based on **average hourly rate**, `fair_pay_score = 1 if hourly_avg_eur >= 13.9 else 0`
- Export: only columns with results; name files as you like under `results/01_fair_pay/`
- Charts (by priority):
  - **Required:** score 0/1 distribution; pass rate by `job_category_names`; hourly (avg) boxplot (by score or category)
  - **Optional useful:** min/avg/max hourly distributions; merge or annotate small categories
  - Skip low-value extras
- All written conclusions apply only to the sample actually analyzed for this topic

### 3–4. Language-level encoding (all jobs)

Encoding:

- German `de_level`: 0 not required / 1 A1–A2 / 2 B1–B2 / 3 C1–C2
- English `en_level`: 1 A1–A2 / 2 B1–B2 / 3 C1–C2 (**no 0**: default at least beginner English)
- Reason columns: `de_reason`, `en_reason`
  - **Rule hit** (tags / CEFR / phrase lexicon): prefix `[rule]`; reason must be bilingual (`中文 / English`)
  - **Rules cannot complete both de/en** (including “no German requirement found” / “default English beginner”): must call AI (DeepSeek); prefix **`[AI辅助]`**; reason must be bilingual
  - **No key / API failure:** prefix `[fallback]`; reason must be bilingual (e.g. default de=0 / en=1)

“Has a tag” = skill tags such as German/English in `job_names` **or** explicit CEFR (A1–C2) in `description`/`title` — both count.

**Priority (strict):**

1. Tags / explicit CEFR / rule phrase lexicon → levels; if multiple levels for the same language, **take the minimum only**
2. **Do not** apply pure-rule defaults “no German context → de=0” or “no English clue → en=1”; treat those as incomplete rules → AI assist
3. If rules still cannot produce **complete** de and en → call DeepSeek for missing items, then posting-language floor:
   - `language=en` → `en_level = max(en_level, 1)`, German unchanged
   - `language=de` → `de_level = max(de_level, 1)`, English unchanged
4. Colloquial phrases (e.g. “fluent German”) go through a **self-built EN/DE phrase→level map** first; only then AI if uncovered

DeepSeek: follow `deepseek_ai_prompt.md`; call when rules cannot complete de/en; reason prefix always `[AI辅助]`.

### 5. Language × job score

- **Sample:** only hourly jobs already Fair Pay–scored
- Form: key counts + charts + short written conclusions
- Output: `results/02_language_vs_score/`

### 6. Bargaining level

- Definition and calculation: fully per `file/en/bargaining_power.md` (clean rules, P, C, z-score, α=0.5 `bargain_score`)
- Sample: bargain-eligible jobs (drop rules in that doc); amounts must already be in EUR
- May cross with German/English levels (readme topic)
- Output: `results/03_language_vs_bargain/`
- Conclusions only for this topic’s actual sample

### Suggested script layout

- Split into:
  - `fair_pay_analysis.py`
  - `language_scoring.py` (phrase lexicon + DeepSeek)
  - `bargain_analysis.py`
  - `main.py` (call in sequence)
