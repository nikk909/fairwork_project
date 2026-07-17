# Cleaned Dataset Description (`dataset.csv`)

**Data file:** `dataset/dataset.csv`  
**Generation script:** `dataset_extact_script.py`  
**Raw source:** `rawdata/dataset_*.json` (Freelancer.com, scraped via Apify `freelancer-scraper`)  
**Encoding:** UTF-8 with BOM (`utf-8-sig`)  
**Format:** CSV, one public project per row

## Overview

| Item | Description |
|------|-------------|
| Rows | **162** (deduplicated by `id`; keep last scrape for same id) |
| Columns | **19** |
| Country scope | Scrape limited to **Germany**; no separate country column in this table |
| Language scope | Mainly **`en`** (120) and **`de`** (42) |
| Pricing type | `fixed` 130; `hourly` 32 |

**Source files (`source_file`):**

- `dataset_freelancer-scraper_2026-06-10_18-23-52-667.json`
- `dataset_freelancer-scraper_2026-07-02_23-54-41-352.json`
- `dataset_freelancer-scraper_2026-07-14_21-45-57-461.json`

> Raw JSON field docs: [`rawdata_description.md`](rawdata_description.md). This table is an analysis subset extracted and flattened from nested raw structures.

---

## Field descriptions

### Identity and content

| Column | Type | Meaning | Missing |
|--------|------|---------|---------|
| `id` | number | Unique Freelancer project ID | None |
| `title` | string | Project title | None |
| `url` | string | Project detail URL | None |
| `description` | string | Full project description (requirements, deliverables, skills, etc.) | None |

### Pricing and budget

| Column | Type | Meaning | Missing |
|--------|------|---------|---------|
| `type` | string | Pricing: `fixed` (lump sum) or `hourly` | None |
| `budget_min` | number | Budget floor. `fixed` = total floor; `hourly` = hourly floor | None |
| `budget_max` | number | Budget ceiling. `fixed` = total ceiling; `hourly` = hourly ceiling | Few missing (~4) |
| `currency_code` | string | ISO currency code, e.g. `EUR`, `USD`, `INR` | None |
| `currency_exchange_rate` | number | Exchange rate vs USD (`USD` = `1`) | None |

Current currency mix (approx.): `EUR` 120, `USD` 36, `INR` 4, plus a few `AUD`, `SGD`.

### Hourly commitment (hourly only)

From raw `hourly_project_info.commitment`. Only populated when `type = hourly`.

| Column | Type | Meaning | Missing |
|--------|------|---------|---------|
| `commitment_hours` | number | Expected hours, e.g. `40` | Empty for `fixed` (130 rows) |
| `commitment_interval` | string | Hourly period; all `week` in this data | Same |

### Skills / category tags

Flattened from raw `jobs[]` (multiple values joined with `", "`):

| Column | Type | Meaning | Example |
|--------|------|---------|---------|
| `job_names` | string | Skill tag names | `Python, Web Scraping` |
| `job_category_names` | string | Category names | `Websites, IT & Software` |
| `job_category_ids` | string | Category IDs | `1, 6` |

### Bid statistics

| Column | Type | Meaning | Missing |
|--------|------|---------|---------|
| `bid_count` | number | Number of bids received | Few missing (~8) |
| `bid_avg` | number | Average bid amount (`fixed` = total; `hourly` = hourly rate) | Same |

### Language and local requirements

| Column | Type | Meaning | Missing |
|--------|------|---------|---------|
| `local` | boolean | Whether local / on-site work is required | Mostly empty (field often not returned); when present `True` / `False` |
| `language` | string | Project **posting language** (e.g. `en`, `de`); not the same as German skill requirement | None |

### Provenance

| Column | Type | Meaning |
|--------|------|---------|
| `source_file` | string | Which raw JSON file this row came from |

---

## Mapping to raw JSON

| CSV column | Raw path |
|------------|----------|
| `id` | `id` |
| `title` | `title` |
| `url` | `url` |
| `description` | `description` |
| `type` | `type` |
| `budget_min` | `budget.minimum` |
| `budget_max` | `budget.maximum` |
| `currency_code` | `currency.code` |
| `currency_exchange_rate` | `currency.exchange_rate` |
| `commitment_hours` | `hourly_project_info.commitment.hours` |
| `commitment_interval` | `hourly_project_info.commitment.interval` |
| `job_names` | `jobs[].name` (joined) |
| `job_category_names` | `jobs[].category.name` (joined) |
| `job_category_ids` | `jobs[].category.id` (joined) |
| `bid_count` | `bid_stats.bid_count` |
| `bid_avg` | `bid_stats.bid_avg` |
| `local` | `local` |
| `language` | `language` |
| `source_file` | (written by script; not a raw field) |

**Not collected:** country (`location.country.name`) — dataset defaults to Germany.

---

## Link to project analyses

| Analysis goal | Main columns |
|---------------|--------------|
| Fair Pay scoring | `type`, `budget_min`, `budget_max`, `currency_code`, `currency_exchange_rate`, `commitment_hours`, `commitment_interval`, `local`, `description` |
| German-level encoding | `description`, `title`, `language`, `job_names` |
| Bargaining power (project level) | `bid_count`, `bid_avg`, `budget_max` |

**Common derived metrics:**

- `bid_ratio = bid_avg / budget_max` (bid relative to budget ceiling)
- Hourly estimates: for `fixed` jobs, infer hours from `description` then convert; use `currency_exchange_rate` to unify to USD or EUR

---

## Data limitations

This table **does not include**:

- Individual bid details (bidder, amount, time)
- Buyer information
- Actual award amount and winner
- Platform fees and payment records
- Post-completion ratings / reviews
- Precise geography (no country column; `local` mostly empty)

Therefore bargaining analysis can only be done at the **project level**.

---

## How to regenerate

From the project root:

```bash
python dataset_extact_script.py
```

Output **overwrites** `dataset/dataset.csv`.
