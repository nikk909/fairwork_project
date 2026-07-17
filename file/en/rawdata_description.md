# Freelancer.com Dataset Field Reference

**Data file:** `data/dataset_freelancer-scraper_2026-06-10_18-23-52-667.json`  
**Source:** [Freelancer.com](https://www.freelancer.com/)  
**Scraper:** Apify `freelancer-scraper`

## Structure overview

The file is a JSON **array**; each element is one **public project** record. This file has **57** projects.

> **Note:** The API does not always return every field — only populated fields are included; unpaid upgrades, empty objects, etc. may be omitted. Fields can differ across records.

---

## 1. Top-level fields

### Identity and content

| Field | Type | Meaning |
|-------|------|---------|
| `id` | number | Unique project ID on Freelancer |
| `title` | string | Project title |
| `url` | string | Project detail URL |
| `description` | string | Full project description (requirements, deliverables, skills, etc.) |
| `preview_description` | string | Truncated preview for list pages (usually ~100 characters) |

### Project type and budget

| Field | Type | Meaning |
|-------|------|---------|
| `type` | string | Pricing: `fixed` (lump sum) or `hourly` |
| `budget` | object | Budget range; see [budget](#budget) |
| `currency` | object | Currency info; see [currency](#currency) |
| `hourly_project_info` | object | **Hourly projects only**; commitment and duration; see [hourly_project_info](#hourly_project_info) |

### Bid statistics

| Field | Type | Meaning |
|-------|------|---------|
| `bid_stats` | object | Bid summary; see [bid_stats](#bid_stats) |
| `bidperiod` | number | Days bidding is open (all `7` in this dataset) |
| `hidebids` | boolean | Whether other freelancers’ bid amounts are hidden |
| `time_free_bids_expire` | string | Free-bid window expiry (ISO 8601 UTC) |

### Status and time

| Field | Type | Meaning |
|-------|------|---------|
| `status` | string | Backend status (all `active` in this dataset) |
| `frontend_project_status` | string | UI status (all `open` — open for bids) |
| `submitdate` | string | Submit date (UTC) |
| `time_submitted` | string | Submit time (UTC) |
| `time_updated` | string | Last update time (UTC) |
| `deleted` | boolean | Whether the project is deleted |

### Language and location

| Field | Type | Meaning |
|-------|------|---------|
| `language` | string | Posting language, e.g. `en`, `de`. Note: posting language ≠ German skill requirement |
| `local` | boolean | Whether local/on-site work is required; when `true`, usually has a concrete `location` |
| `location` | object | Geography; see [location](#location) |

### Skill tags

| Field | Type | Meaning |
|-------|------|---------|
| `jobs` | array | Linked skill/category tags; see [jobs[]](#jobs) |

### Platform features and paid upgrades

| Field | Type | Meaning |
|-------|------|---------|
| `upgrades` | object | Paid upgrades purchased by the employer; see [upgrades](#upgrades) |
| `featured` | boolean | Featured / pinned listing |
| `urgent` | boolean | Marked urgent |
| `assisted` | boolean | Freelancer assisted / recruiter service |
| `hireme` | boolean | Hire Me direct-hire mode |
| `nonpublic` | boolean | Non-public project |
| `active_prepaid_milestone` | object | Prepaid milestone info (often `{}`) |

### Enterprise and compliance

| Field | Type | Meaning |
|-------|------|---------|
| `enterprise_ids` | array | Linked enterprise account IDs (usually empty) |
| `enterprises` | array | Enterprise details (usually empty) |
| `group_ids` | array | User group IDs (usually empty) |
| `pool_ids` | array | Talent pool IDs; often `[1]` (public pool) in this dataset |
| `is_buyer_kyc_required` | boolean | Whether the buyer must complete KYC |
| `is_seller_kyc_required` | boolean | Whether the freelancer must complete KYC |
| `is_escrow_project` | boolean | Whether payment is via platform escrow |

---

## 2. Nested objects

### budget

| Field | Type | Meaning |
|-------|------|---------|
| `minimum` | number | Budget floor. `fixed` = total floor; `hourly` = hourly floor |
| `maximum` | number | Budget ceiling. `fixed` = total ceiling; `hourly` = hourly ceiling |

### bid_stats

| Field | Type | Meaning |
|-------|------|---------|
| `bid_count` | number | Number of bids received |
| `bid_avg` | number | Average bid amount (`fixed` = total; `hourly` = hourly rate) |

### currency

| Field | Type | Meaning |
|-------|------|---------|
| `id` | number | Freelancer internal currency ID |
| `code` | string | ISO currency code, e.g. `EUR`, `USD`, `INR`, `AUD` |
| `name` | string | Currency name, e.g. `Euro` |
| `sign` | string | Currency symbol, e.g. `€`, `$`, `₹` |
| `country` | string | Related region code, e.g. `EU`, `US`, `IN` |
| `exchange_rate` | number | Rate vs USD (`USD` = `1`) |
| `is_escrowcom_supported` | boolean | Whether Escrow.com is supported |
| `is_external` | boolean | Whether external / non-standard platform currency (only some records) |

### hourly_project_info

Only present when `type: "hourly"`.

| Field | Type | Meaning |
|-------|------|---------|
| `commitment.hours` | number | Expected hours, e.g. `40` |
| `commitment.interval` | string | Period, e.g. `week` |
| `duration_enum` | string | Duration enum; all `unspecified` in this dataset |

### location

| Field | Type | Meaning |
|-------|------|---------|
| `country` | object | Country info; `{}` when no location; otherwise includes `name` |
| `country.name` | string | Country name, e.g. `Saudi Arabia` |
| `administrative_area` | string | State/province, e.g. `Eastern Province` |
| `vicinity` | string | City/area, e.g. `Dhahran` |
| `latitude` | number | Latitude |
| `longitude` | number | Longitude |
| `timezone` | object | Timezone (often `{}` in this dataset) |

### jobs[]

Each element in `jobs` is a skill/category tag.

| Field | Type | Meaning |
|-------|------|---------|
| `id` | number | Skill tag ID |
| `name` | string | Skill name, e.g. `Python`, `German Translator` |
| `seo_url` | string | URL slug, e.g. `web_scraping` |
| `local` | boolean | Whether the skill is marked local (optional) |
| `category.id` | number | Parent category ID |
| `category.name` | string | Parent category name, e.g. `Websites, IT & Software` |

### upgrades

Paid upgrades purchased by the employer. Most records list only `true` items; some (e.g. the first) list all boolean fields.

| Field | Meaning |
|-------|---------|
| `listed` | Publicly listed (almost always `true`) |
| `assisted` | Platform assisted / recruiter service |
| `recruiter` | Recruiter assistance |
| `pf_only` | Preferred Freelancer Only |
| `ip_contract` | Includes IP contract terms |
| `NDA` | Non-Disclosure Agreement |
| `sealed` | Sealed bids (bidders cannot see others’ amounts) |
| `featured` | Featured / pinned |
| `urgent` | Urgent flag |
| `premium` | Premium project |
| `fulltime` | Full-time nature |
| `qualified` | Restricted to certified/qualified freelancers |
| `enterprise` | Enterprise project |
| `nonpublic` | Non-public |
| `non_compete` | Non-compete clause |
| `project_management` | Includes project management service |
| `active_prepaid_milestone` | Prepaid milestone (nested object) |

---

## 3. Link to project analyses

| Analysis goal | Main fields |
|---------------|-------------|
| Fair Pay scoring | `type`, `budget`, `currency`, `hourly_project_info`, `local`, `location`, `description` |
| German-level encoding | `description`, `title`, `language`, `jobs[].name` |
| Bargaining power (project level) | `bid_stats.bid_count`, `bid_stats.bid_avg`, `budget.maximum` |

**Common derived metrics:**

- `bid_ratio = bid_stats.bid_avg / budget.maximum` (bid relative to budget ceiling)
- Hourly estimates: for `fixed` jobs, infer hours from `description` then convert

---

## 4. Data limitations

This dataset **does not include**:

- Individual bid details (bidder, amount, time)
- Buyer information
- Actual award amount and winning freelancer
- Platform fees and payment records
- Post-completion ratings / reviews

Therefore bargaining analysis can only be done at the **project level**, not at the individual bidder level.
