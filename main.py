"""Entry point: run all three analysis topics in order."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

import bargain_analysis
import fair_pay_analysis
import language_scoring
from currency_utils import add_eur_columns

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset" / "dataset.csv"


def main() -> None:
    df = pd.read_csv(DATASET, encoding="utf-8-sig")
    df = add_eur_columns(df)

    # Language first so Fair Pay factor correlation can use de/en levels.
    lang_df = language_scoring.score_languages(df, ROOT / "results" / "02_language_vs_score")
    fair_df = fair_pay_analysis.run(lang_df, ROOT / "results" / "01_fair_pay")
    language_scoring.analyze_vs_fair_pay(
        lang_df, fair_df, ROOT / "results" / "02_language_vs_score"
    )
    bargain_analysis.run(lang_df, ROOT / "results" / "03_language_vs_bargain")


if __name__ == "__main__":
    main()
