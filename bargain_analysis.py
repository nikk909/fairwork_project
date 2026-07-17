"""Topic 3: bargaining power + language cross-analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

EXPORT_COLS = [
    "id",
    "title",
    "type",
    "de_level",
    "en_level",
    "de_reason",
    "en_reason",
    "bid_count",
    "budget_min_eur",
    "budget_max_eur",
    "bid_avg_eur",
    "P",
    "C",
    "z_P",
    "z_C",
    "bargain_score",
    "bargain_tier",
    "url",
]


def _ensure_out_dir(out_dir: str | Path) -> Path:
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _assign_tier(scores: pd.Series) -> pd.Series:
    q1 = scores.quantile(0.25)
    q3 = scores.quantile(0.75)

    def tier(v: float) -> str:
        if v <= q1:
            return "low"
        if v >= q3:
            return "high"
        return "mid"

    return scores.map(tier)


def _plot_hist(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df["bargain_score"].dropna(), bins=20, color="#4c72b0", edgecolor="white")
    ax.set_xlabel("bargain_score")
    ax.set_ylabel("count")
    ax.set_title(f"Bargain score distribution (n={len(df)})")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_level_vs_bargain(df: pd.DataFrame, level_col: str, out_path: Path) -> None:
    title_map = {
        "de_level": "German requirement level vs bargain score",
        "en_level": "English requirement level vs bargain score",
    }
    levels = sorted(df[level_col].dropna().unique())
    data = [df.loc[df[level_col] == lv, "bargain_score"].dropna() for lv in levels]
    fig, ax = plt.subplots(figsize=(7, 4))
    if any(len(d) > 0 for d in data):
        ax.boxplot(data, tick_labels=[str(lv) for lv in levels], showfliers=True)
    ax.set_xlabel(level_col)
    ax.set_ylabel("bargain_score")
    ax.set_title(f"{title_map.get(level_col, level_col)} (n={len(df)})")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _spearman(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    """Spearman ρ via Pearson on ranks (no scipy dependency)."""
    pair = pd.concat([x, y], axis=1).dropna()
    n = len(pair)
    if n < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return float("nan"), n
    return float(pair.iloc[:, 0].rank().corr(pair.iloc[:, 1].rank())), n


def _cross_bargain(df: pd.DataFrame, level_col: str) -> pd.DataFrame:
    return (
        df.groupby(level_col, dropna=False)
        .agg(
            n=("bargain_score", "size"),
            mean_bargain=("bargain_score", "mean"),
            median_bargain=("bargain_score", "median"),
        )
        .reset_index()
        .sort_values(level_col)
    )


def _plot_de_en_bargain_comparison(
    df: pd.DataFrame,
    rho_de: float,
    rho_en: float,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, level_col, title, rho in [
        (axes[0], "de_level", "German requirement (de_level)", rho_de),
        (axes[1], "en_level", "English requirement (en_level)", rho_en),
    ]:
        levels = sorted(df[level_col].dropna().unique())
        data = [df.loc[df[level_col] == lv, "bargain_score"].dropna() for lv in levels]
        if any(len(d) > 0 for d in data):
            ax.boxplot(data, tick_labels=[str(lv) for lv in levels], showfliers=True)
        rho_txt = f"{rho:.3f}" if pd.notna(rho) else "nan"
        ax.set_title(f"{title}\nSpearman rho={rho_txt}")
        ax.set_xlabel(level_col)
    axes[0].set_ylabel("bargain_score")
    fig.suptitle(f"German vs English x bargain comparison (n={len(df)})", y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _write_conclusion(
    df: pd.DataFrame,
    cross_de: pd.DataFrame,
    cross_en: pd.DataFrame,
    rho_de: float,
    rho_en: float,
    out_path: Path,
) -> None:
    n = len(df)
    mean = float(df["bargain_score"].mean()) if n else float("nan")
    median = float(df["bargain_score"].median()) if n else float("nan")
    q1 = float(df["bargain_score"].quantile(0.25)) if n else float("nan")
    q3 = float(df["bargain_score"].quantile(0.75)) if n else float("nan")

    if pd.isna(rho_de) and pd.isna(rho_en):
        stronger = "无法判断"
    elif pd.notna(rho_de) and (pd.isna(rho_en) or abs(rho_de) >= abs(rho_en)):
        stronger = "德语"
    else:
        stronger = "英语"

    lines = [
        "# 语言 × 议价结论",
        "",
        f"- 议价可算样本 n = {n}",
        f"- bargain_score：均值 = {mean:.3f}，中位数 = {median:.3f}，Q1 = {q1:.3f}，Q3 = {q3:.3f}",
        "",
        "## 对比数值（Spearman ρ vs bargain_score）",
        f"- 德语 de_level：ρ = {rho_de:.3f}" if pd.notna(rho_de) else "- 德语 de_level：ρ = nan",
        f"- 英语 en_level：ρ = {rho_en:.3f}" if pd.notna(rho_en) else "- 英语 en_level：ρ = nan",
        f"- |ρ| 更大者：{stronger}（描述性比较，非因果）",
        "",
        "## 按 de_level 的 bargain",
    ]
    for _, row in cross_de.iterrows():
        lines.append(
            f"- de_level={int(row.de_level)}: n={int(row.n)}, "
            f"mean={row.mean_bargain:.3f}, median={row.median_bargain:.3f}"
        )
    lines.append("")
    lines.append("## 按 en_level 的 bargain")
    for _, row in cross_en.iterrows():
        lines.append(
            f"- en_level={int(row.en_level)}: n={int(row.n)}, "
            f"mean={row.mean_bargain:.3f}, median={row.median_bargain:.3f}"
        )
    lines.append("")
    lines.append("## 按 type（fixed vs hourly）分组简述")
    for t, g in df.groupby("type"):
        lines.append(f"- type={t}: n={len(g)}, mean bargain={g['bargain_score'].mean():.3f}")
    lines.extend(
        [
            "",
            "## 观察",
            "- 三张对比图：`de_level_vs_bargain.png`、`en_level_vs_bargain.png`、`de_vs_en_bargain_comparison.png`。",
            "",
            "## 局限",
            "- 项目级代理指标；无成交价与单个投标明细。",
            "- fixed 与 hourly 合表做一次 z-score 标准化；两类金额含义不同（总价 vs 时薪），解释时需谨慎。",
            "- 语言为岗位要求编码，非工人实际能力；结论仅描述本样本。",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def run(df_with_lang: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    """Clean → bargain scores → language cross plots/结论; return scored table."""
    out = _ensure_out_dir(out_dir)

    needed = ["bid_count", "bid_avg_eur", "budget_min_eur", "budget_max_eur", "de_level", "en_level"]
    missing = [c for c in needed if c not in df_with_lang.columns]
    if missing:
        raise ValueError(f"Input missing columns: {missing}")

    sub = df_with_lang.dropna(
        subset=["bid_count", "bid_avg_eur", "budget_min_eur", "budget_max_eur"]
    ).copy()
    sub = sub[sub["budget_max_eur"] > sub["budget_min_eur"]].copy()

    sub["P"] = (sub["bid_avg_eur"] - sub["budget_min_eur"]) / (
        sub["budget_max_eur"] - sub["budget_min_eur"]
    )
    sub["C"] = np.log1p(sub["bid_count"])
    sub["z_P"] = (sub["P"] - sub["P"].mean()) / sub["P"].std(ddof=0)
    sub["z_C"] = (sub["C"] - sub["C"].mean()) / sub["C"].std(ddof=0)
    alpha = 0.5
    sub["bargain_score"] = alpha * sub["z_P"] - (1 - alpha) * sub["z_C"]
    sub["bargain_tier"] = _assign_tier(sub["bargain_score"])

    export = sub[[c for c in EXPORT_COLS if c in sub.columns]].copy()
    export.to_csv(out / "bargain_scored.csv", index=False, encoding="utf-8-sig")

    cross_de = _cross_bargain(sub, "de_level")
    cross_en = _cross_bargain(sub, "en_level")
    cross_de.to_csv(out / "cross_de.csv", index=False, encoding="utf-8-sig")
    cross_en.to_csv(out / "cross_en.csv", index=False, encoding="utf-8-sig")

    rho_de, n_de = _spearman(sub["de_level"], sub["bargain_score"])
    rho_en, n_en = _spearman(sub["en_level"], sub["bargain_score"])
    compare = pd.DataFrame(
        [
            {
                "language": "de",
                "level_col": "de_level",
                "n": n_de,
                "spearman_vs_bargain_score": rho_de,
                "abs_spearman": abs(rho_de) if pd.notna(rho_de) else float("nan"),
            },
            {
                "language": "en",
                "level_col": "en_level",
                "n": n_en,
                "spearman_vs_bargain_score": rho_en,
                "abs_spearman": abs(rho_en) if pd.notna(rho_en) else float("nan"),
            },
        ]
    )
    compare.to_csv(out / "de_vs_en_comparison.csv", index=False, encoding="utf-8-sig")

    _plot_hist(sub, out / "bargain_score_hist.png")
    _plot_level_vs_bargain(sub, "de_level", out / "de_level_vs_bargain.png")
    _plot_level_vs_bargain(sub, "en_level", out / "en_level_vs_bargain.png")
    _plot_de_en_bargain_comparison(sub, rho_de, rho_en, out / "de_vs_en_bargain_comparison.png")
    _write_conclusion(sub, cross_de, cross_en, rho_de, rho_en, out / "结论.md")

    return sub
