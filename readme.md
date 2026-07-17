# Project overview: Fair Pay and language requirements on Freelancer.com (Germany)

**English** | [中文](README.zh-CN.md)

MSK 6 Research Project (Fairwork Pilots). This repository documents: scraping Germany-related projects from a public platform, applying an approximate Fairwork **Fair Pay** score, and describing how German / English job-language requirements relate to that score and to a bargaining proxy.

---

## 1. What this project does

In the gig / platform economy, Fairwork evaluates platforms against a set of principles. This project focuses on one of them:

**Fair Pay**

Together with the **German / English language requirements** commonly seen on Freelancer.com (Germany-related posts), it does three things:

1. Use public project budgets to approximate whether a posting meets the German minimum wage line (Fair Pay scoring).
2. Encode German and English requirement levels from job text.
3. Build a project-level bargaining proxy from bid statistics, then describe it by language level.

**Research question:**  
In this Germany-related Freelancer.com sample, what descriptive relationships appear between stated German / English requirement levels and (a) Fair Pay scores and (b) the bargaining proxy? How do the German and English associations compare in strength?

This project does **not** make causal claims; results are in-sample description only.

---

## 2. How Fair Pay is operationalised here

Fairwork Principle 1 roughly includes:

| Clause | Meaning | This project |
|------|------|------------|
| **1.1** | After work-related costs, active hours at least meet the local minimum wage (or a higher sectoral collective agreement wage) | Compare public hourly budgets to the German statutory minimum wage; pass = **1**, else **0** |
| **1.2** | Meet the local living wage | The living-wage reference used in the Germany Fairwork report is below the statutory minimum, so this project **does not add a separate living-wage point**; the effective threshold is the minimum wage |

**Threshold used here:**

> Mean hourly rate (EUR) ≥ **€13.90 / hour** → `fair_pay_score = 1`, else `= 0`

Note: public postings do not show true costs, unpaid waiting time, platform fees, or whether pay is on time and in full. This is an approximation of whether the **budget clears the line**, **not** a full Fairwork platform audit.

---

## 3. Data source and shape

| Item | Detail |
|----|------|
| Platform | Public project pages on [Freelancer.com](https://www.freelancer.com/) |
| Scrape | [Apify](https://apify.com/) `freelancer-scraper` |
| Cleaned table | `dataset/dataset.csv` (built from `rawdata/` JSON via `dataset_extact_script.py`) |
| Sample size | **162** projects after deduplicating on `id` (Germany-related scrape) |
| Posting language | Mostly English (~120) and German (~42) |
| Pricing type | **Fixed** 130; **hourly** 32 |

**Pricing types:**

- **Fixed:** one total budget range for the whole job (e.g. €500–800 to complete).
- **Hourly:** an hourly budget range (e.g. €15–25 / hour).

Fair Pay scoring mainly uses **hourly** jobs, which can be compared directly to €13.90 / hour. Fixed jobs lack reliable hours, so this project does not assign them a Fair Pay score.

Field notes, limits, and regeneration: `file/dataset说明.md`. Raw JSON fields: `file/rawdata说明.md`.

**What the data does not include (and thus constrains analysis):**

- Individual bidder detail, award price, or winner
- Employer information, platform fees, payment records
- Post-completion ratings
- Workers’ true language ability or take-home pay

---

## 4. Pipeline (what was run)

Entry point: `main.py` (language coding → Fair Pay → language × score → bargaining).

```
rawdata/*.json
    → dataset_extact_script.py → dataset/dataset.csv
    → main.py
         ├─ Convert currency to EUR (currency_utils)
         ├─ Encode language levels (language_scoring)
         ├─ Fair Pay scoring and descriptive correlations (fair_pay_analysis)
         ├─ Language × Fair Pay cross-tabs
         └─ Bargaining proxy × language (bargain_analysis)
```

### 4.1 Currency

Budgets and bids are converted to euro columns so they can be compared with the German minimum wage. Script: `currency_utils.py`.

### 4.2 Language-level coding

Script: `language_scoring.py`. From title, description, skill tags, posting language, etc., each project gets:

| Variable | Values | Meaning |
|------|------|------|
| `de_level` | 0 / 1 / 2 / 3 | No German required → basic A1/A2 → fluent B1/B2 → strong C1/C2 |
| `en_level` | 1 / 2 / 3 | Beginner → intermediate/fluent → proficient |

**Coding steps:**

1. **Rule matching:** keyword / phrase lists (e.g. `fluent german`, `kein deutsch`) and skill tags (e.g. `German`, `English`); when multiple levels hit, take the lower requirement tier.
2. **AI assist:** if either side cannot be decided by rules, call **DeepSeek** (`deepseek-v4-pro`) on the public job text for level + reason; reason prefix `[AI辅助]`. Requires `DEEPSEEK_API_KEY` (see `.env`).
3. **Posting-language floor:** e.g. if posting language is `en`, English is at least beginner.
4. **Final fallback:** if AI still fails, German defaults to 0 and English to 1, with reason tagged `[fallback]`.

Full-sample language output: `results/02_language_vs_score/language_all.csv`.

### 4.3 Fair Pay scoring

Script: `fair_pay_analysis.py`.

- Keep only `type = hourly` with complete euro budget columns.
- Compute mean hourly rate `hourly_avg_eur` from budget min/max.
- Compare to 13.90 to get `fair_pay_score` (0/1).
- Also export Spearman correlations between selected factors and score / wage (association strength only; not causal).

Scorable sample: **n = 28** (32 hourly total; some excluded for incomplete budget/FX fields).

Output: `results/01_fair_pay/`.

### 4.4 Language × Fair Pay

On the 28 scored rows, summarise pass rates by `de_level` / `en_level` and compute Spearman ρ between language level and `fair_pay_score`.

Output: `results/02_language_vs_score/`.

### 4.5 Bargaining proxy

Script: `bargain_analysis.py`. Formula notes: `file/议价能力.md`.

Without individual bids or award prices, only a **project-level** proxy `bargain_score` is constructed:

1. **Price position \(P\)**: relative position of mean bid `bid_avg` in `[budget_min, budget_max]`.
2. **Competition \(C\)**: `log(1 + bid_count)`.
3. Z-score \(P\) and \(C\), then:  
   `bargain_score = 0.5 * z(P) - 0.5 * z(C)`  
   (higher relative bids and fewer bidders → higher score.)

Computable sample: **n = 151** (requires complete bid count, mean bid, and budget bounds with max > min).

Output: `results/03_language_vs_bargain/`.

---

## 5. Results (descriptive)

Figures below come from the current `results/` conclusions and cross-tabs. They report in-sample observations only—no causal explanation or policy advice.

### 5.1 Fair Pay (hourly, n = 28)

| Metric | Value |
|------|------|
| Pass (score = 1) | 19 |
| Fail (score = 0) | 9 |
| Pass rate | 67.9% |
| Median mean hourly wage | €14.83 / h |
| Mean of mean hourly wage | €17.19 / h |
| Threshold | €13.90 / h |

Spearman ρ vs `fair_pay_score` (same sample; n as in table):

| Factor | ρ | n |
|------|-----|---|
| German requirement `de_level` | 0.499 | 28 |
| Posting language German | 0.474 | 28 |
| English requirement `en_level` | −0.273 | 28 |
| Bid count `bid_count` | 0.183 | 26 |
| Number of skill tags | −0.112 | 28 |

Charts: `results/01_fair_pay/` (score distribution, wage boxplots, correlation bars, etc.).

### 5.2 Language level × Fair Pay pass rate (n = 28)

**German `de_level`**

| de_level | n | Pass rate |
|----------|---|--------|
| 0 (not required) | 18 | 50.0% |
| 1 | 5 | 100% |
| 2 | 3 | 100% |
| 3 | 2 | 100% |

**English `en_level`**

| en_level | n | Pass rate |
|----------|---|--------|
| 1 | 14 | 78.6% |
| 2 | 11 | 63.6% |
| 3 | 3 | 33.3% |

Spearman ρ vs `fair_pay_score`: German **0.499**, English **−0.273** (larger \|ρ\| for German).

Charts: `results/02_language_vs_score/`.

### 5.3 Language level × bargaining (n = 151)

| Metric | Value |
|------|------|
| Mean `bargain_score` | 0.000 |
| Median | −0.028 |
| Q1 / Q3 | −0.401 / 0.299 |

Spearman ρ vs `bargain_score`: German **0.180**, English **0.183**.

**By de_level**

| de_level | n | Mean | Median |
|----------|---|------|--------|
| 0 | 104 | −0.043 | −0.121 |
| 1 | 17 | 0.039 | 0.016 |
| 2 | 14 | 0.178 | 0.137 |
| 3 | 16 | 0.084 | 0.188 |

**By en_level**

| en_level | n | Mean | Median |
|----------|---|------|--------|
| 1 | 107 | −0.095 | −0.125 |
| 2 | 37 | 0.261 | 0.167 |
| 3 | 7 | 0.076 | 0.174 |

**By pricing type**

| type | n | Mean bargain |
|------|---|--------------|
| fixed | 125 | −0.017 |
| hourly | 26 | 0.081 |

Charts: `results/03_language_vs_bargain/`.

---

## 6. Limitations (fuller list)

### 6.1 Data and sample

- **Limited n:** 162 cleaned rows; only **28** hourly rows for Fair Pay. High German / English cells often have single-digit counts, so pass rates and means are noisy and should not be extrapolated.
- **Platform / country scope:** Freelancer.com and a Germany-related scrape window only; not all German gig platforms or other countries.
- **Scrape window:** several Apify public-list pulls, not a full historical archive; open / popular jobs may be over-represented.
- **Incomplete public fields:** `local` (on-site) often missing; no precise city or employer type.

### 6.2 Fair Pay scoring itself

- **No cost deduction:** Fairwork 1.1 requires meeting the minimum **after** costs. This project uses gross budgeted hourly rates only (no software, equipment, tax, platform fees, unpaid coordination time).
- **Payment not verified:** no visibility into timely/full payment, contracts, or chargebacks.
- **Fixed jobs unscored:** 130 fixed jobs lack reliable hours, so Fair Pay findings **cannot** be generalised to fixed-price work.
- **Living-wage clause simplified:** because the reference living wage is below the statutory minimum, scoring reduces to a 0/1 check against ≥ 13.90, not the full 1.1+1.2 dual-point structure.
- **Budget ≠ award price:** `budget_*` is the employer’s posted range; actual awards may be lower or higher.

### 6.3 Language coding

- Codes **stated job requirements** (what the text says), not workers’ true German/English ability or native-speaker status.
- **Rules + AI:** keywords can miss or mis-hit; DeepSeek may be unstable on vague text. Re-running with another model or prompt can change tiers.
- **Defaults:** English often floored at “at least beginner”; failed German rules default to “not required”, which can shift tier shares.
- Posting language (`language`) ≠ ability requirement: an English post may still require German—judged from the description.

### 6.4 Bargaining proxy

- **Project-level proxy only:** combines relative bid position and bidder count; **not** individual worker bargaining outcomes or award prices.
- **Fixed and hourly standardised together:** total price and hourly rates differ in scale; even after z-scores, cross-type comparison needs care.
- No bid timeline or award price, so cases like “fierce competition but high final award” cannot be separated.

### 6.5 Statistical and interpretive bounds

- Reported Spearman ρ, group means, and pass rates are **descriptive associations**.
- **Correlation ≠ causation:** one cannot claim that “raising German requirements causes higher Fair Pay” or that “English requirements cause lower pass rates.”
- No multivariate regression or confounder control (skill category, difficulty, employer location, etc. may jointly affect language and budget).

### 6.6 Ethics and method bounds

- Public job ads only; no worker interviews and no identifiable personal data—suitable for a term project, but lacking first-hand worker evidence.
- AI labelling depends on an external API and key; reproducibility depends on model version and prompts.

---

## 7. How to run

Dependencies: `requirements.txt`. From the project root:

```bash
pip install -r requirements.txt
```

Rebuild the CSV from raw JSON if needed:

```bash
python dataset_extact_script.py
```

Run the full analysis (without `DEEPSEEK_API_KEY`, rows the rules cannot decide fall back):

```bash
python main.py
```

Outputs:

| Directory | Contents |
|------|------|
| `results/01_fair_pay/` | Fair Pay scores, correlation tables, plots, conclusions |
| `results/02_language_vs_score/` | Full language table, cross with Fair Pay |
| `results/03_language_vs_bargain/` | Bargaining scores, cross with language |

Per-folder chart notes: `说明.md`; short write-ups: `结论.md`.

---

## 8. Other docs in the repo

| Path | Purpose |
|------|------|
| `file/研究目标.md` | Research aims and Fair Pay principle excerpts |
| `file/fair pay对应打分.md` | German minimum-wage threshold notes |
| `file/议价能力.md` | Bargaining formula definition |
| `file/实现方案.md` / `file/数据处理.md` | Implementation and cleaning notes |
| `file/评价标准/` | Course Assessment Brief and rubric |
| `deepseek_ai_prompt.md` | Notes related to the language-labelling prompt |
