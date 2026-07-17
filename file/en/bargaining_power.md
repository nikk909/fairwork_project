# Bargaining Power Definition (Project Level)

**Data source:** `dataset/dataset.csv`. This dataset does not include individual bid details, winning prices, or buyer information. Bargaining power can only be constructed as a **project-level** proxy from bid statistics and the budget range.

**Fields used:** `bid_count`, `bid_avg`, `budget_min`, `budget_max` (optional control: `type`).

---

## 0. Sample cleaning

Drop rows that meet any of the following:

- Missing `bid_count` / `bid_avg` / `budget_min` / `budget_max`
- `budget_max <= budget_min` (denominator zero or negative; interval position undefined)

Note: `bid_count` and `bid_avg` have a small number of missing values (~8 rows); drop them for the analysis.

---

## 1. Two raw indicators

**Price position \(P\)** (higher → stronger worker-side bargaining): relative position of the average bid within the employer budget interval \([budget\_min, budget\_max]\).

\[
P_i = \frac{bid\_avg_i - budget\_min_i}{budget\_max_i - budget\_min_i}
\]

| Value | Meaning |
|------|---------|
| `> 1` | Average bid above budget maximum |
| `0 ~ 1` | Within the budget interval |
| `< 0` | Below budget minimum |

**Competition intensity \(C\)** (higher → weaker worker-side bargaining): log of bid count to dampen extreme values.

\[
C_i = \log(1 + bid\_count_i)
\]

---

## 2. Standardization

\(P\) and \(C\) have different scales. Before combining, apply z-scores on the **full cleaned sample**:

\[
z(P_i) = \frac{P_i - \bar{P}}{s_P}, \quad
z(C_i) = \frac{C_i - \bar{C}}{s_C}
\]

where \(\bar{P}\), \(s_P\) are the sample mean and standard deviation of \(P\) (same for \(C\)).

---

## 3. Composite bargaining score

\[
Bargain_i = \alpha \cdot z(P_i) - (1 - \alpha) \cdot z(C_i)
\]

Default **\(\alpha = 0.5\)** (equal weight), i.e.:

\[
Bargain_i = 0.5 \cdot z(P_i) - 0.5 \cdot z(C_i)
\]

Interpretation: bids closer to (or above) the top of the budget range, and fewer competitors → higher \(Bargain\) → stronger worker bargaining power.

---

## 4. Optional: discretize into high / mid / low

Bin by quantiles of `bargain_score` for cross-tabs with German/English levels:

- **Low:** ≤ first quartile (Q1)
- **Mid:** Q1–Q3
- **High:** ≥ third quartile (Q3)

Or split into high/low at the median.

---

## 5. Implementation sketch (Python)

```python
import numpy as np

df = df.dropna(subset=["bid_count", "bid_avg", "budget_min", "budget_max"])
df = df[df["budget_max"] > df["budget_min"]].copy()

df["P"] = (df["bid_avg"] - df["budget_min"]) / (df["budget_max"] - df["budget_min"])
df["C"] = np.log1p(df["bid_count"])

df["z_P"] = (df["P"] - df["P"].mean()) / df["P"].std(ddof=0)
df["z_C"] = (df["C"] - df["C"].mean()) / df["C"].std(ddof=0)

alpha = 0.5
df["bargain_score"] = alpha * df["z_P"] - (1 - alpha) * df["z_C"]
```

---

## Notes

- For `fixed` vs `hourly`, `bid_avg` / budget mean different things (total price vs hourly rate). The ratio \(P\) is still comparable within a project, but if comparing absolute levels or by type, prefer grouping or separate standardization.
- Before computing \(P\), convert `budget_min` / `budget_max` / `bid_avg` to EUR (same as step 1 in `file/en/data_processing.md`: `amount_EUR = amount_original × rate_original / rate_EUR`).
