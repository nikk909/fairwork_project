"""Currency conversion helpers: amounts → EUR."""

from __future__ import annotations

import pandas as pd


def add_eur_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add budget_min_eur, budget_max_eur, bid_avg_eur using USD-relative rates.

    金额_EUR = 金额_原币 × rate_原币 / rate_EUR
    """
    out = df.copy()
    eur_rates = out.loc[out["currency_code"] == "EUR", "currency_exchange_rate"].dropna()
    if eur_rates.empty:
        raise ValueError("No EUR rows found to determine rate_EUR; check currency_code.")

    mode = eur_rates.mode()
    rate_eur = float(mode.iloc[0]) if not mode.empty else float(eur_rates.iloc[0])
    rate_row = out["currency_exchange_rate"]

    for col in ("budget_min", "budget_max", "bid_avg"):
        out[f"{col}_eur"] = out[col] * rate_row / rate_eur

    return out
