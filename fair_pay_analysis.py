"""Topic 1: Fair Pay scoring for hourly jobs + factor correlation."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd

FAIR_PAY_THRESHOLD_EUR = 13.9
TOP_N_FACTORS = 3

EXPORT_COLS = [
    "id",
    "title",
    "type",
    "job_category_names",
    "currency_code",
    "budget_min_eur",
    "budget_max_eur",
    "hourly_min_eur",
    "hourly_avg_eur",
    "hourly_max_eur",
    "fair_pay_score",
    "url",
]

# Predictors that are not definitionally the same as hourly_avg / fair_pay_score.
# Excludes budget_spread (max-min of the same wage range used to score).
# Labels are English (used in charts); Chinese kept in 结论.md via FACTOR_LABEL_ZH.
FACTOR_SPECS: list[tuple[str, str]] = [
    ("de_level", "German requirement level"),
    ("en_level", "English requirement level"),
    ("bid_count", "Bid count"),
    ("commitment_hours", "Weekly commitment hours"),
    ("n_skills", "Number of skill tags"),
    ("language_is_de", "Posting language is German"),
    ("has_local", "On-site / local required"),
]

FACTOR_LABEL_ZH: dict[str, str] = {
    "de_level": "德语要求水平",
    "en_level": "英语要求水平",
    "bid_count": "投标人数",
    "commitment_hours": "每周承诺工时",
    "n_skills": "技能标签数",
    "language_is_de": "发帖语言为德语",
    "has_local": "要求本地/现场",
}


def _ensure_out_dir(out_dir: str | Path) -> Path:
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _prepare_factor_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "job_names" in out.columns:
        out["n_skills"] = (
            out["job_names"]
            .fillna("")
            .astype(str)
            .map(lambda s: len([t.strip() for t in s.replace(";", ",").split(",") if t.strip()]))
        )
    else:
        out["n_skills"] = np.nan
    if "language" in out.columns:
        out["language_is_de"] = (out["language"].astype(str).str.lower() == "de").astype(float)
    else:
        out["language_is_de"] = np.nan
    if "local" in out.columns:
        # True = on-site/local required; False/NaN = not required or unknown
        out["has_local"] = (
            out["local"].map({True: 1.0, "True": 1.0, False: 0.0, "False": 0.0})
        )
    else:
        out["has_local"] = np.nan
    return out


def _spearman(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    """Spearman ρ via Pearson on ranks (no scipy dependency)."""
    pair = pd.concat([x, y], axis=1).dropna()
    n = len(pair)
    if n < 3:
        return float("nan"), n
    if pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return float("nan"), n
    rho = pair.iloc[:, 0].rank().corr(pair.iloc[:, 1].rank())
    return float(rho), n


def _compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for col, label in FACTOR_SPECS:
        if col not in df.columns:
            continue
        rho_score, n_score = _spearman(df[col], df["fair_pay_score"])
        rho_wage, n_wage = _spearman(df[col], df["hourly_avg_eur"])
        rows.append(
            {
                "factor": col,
                "label": label,
                "n_vs_score": n_score,
                "spearman_vs_fair_pay_score": rho_score,
                "abs_spearman_vs_score": abs(rho_score) if pd.notna(rho_score) else np.nan,
                "n_vs_wage": n_wage,
                "spearman_vs_hourly_avg_eur": rho_wage,
                "abs_spearman_vs_wage": abs(rho_wage) if pd.notna(rho_wage) else np.nan,
            }
        )
    corr = pd.DataFrame(rows)
    if corr.empty:
        return corr
    return corr.sort_values("abs_spearman_vs_score", ascending=False, na_position="last")


def _plot_score_distribution(df: pd.DataFrame, out_path: Path) -> None:
    n = len(df)
    counts = df["fair_pay_score"].value_counts().reindex([0, 1], fill_value=0)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(counts.index.astype(str), counts.values, color=["#c44e52", "#4c72b0"])
    ax.set_xlabel("fair_pay_score")
    ax.set_ylabel("count")
    ax.set_title(f"Fair Pay score distribution (n={n})")
    for i, v in enumerate(counts.values):
        ax.text(i, v + 0.1, str(int(v)), ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_hourly_avg_boxplot(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    data = [
        df.loc[df["fair_pay_score"] == 0, "hourly_avg_eur"].dropna(),
        df.loc[df["fair_pay_score"] == 1, "hourly_avg_eur"].dropna(),
    ]
    ax.boxplot(data, tick_labels=["score=0", "score=1"], showfliers=True)
    ax.axhline(FAIR_PAY_THRESHOLD_EUR, color="red", linestyle="--", label=f"threshold={FAIR_PAY_THRESHOLD_EUR}")
    ax.set_ylabel("hourly_avg_eur")
    ax.set_title(f"Hourly avg wage by Fair Pay score (n={len(df)})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_factor_correlation(corr: pd.DataFrame, out_path: Path) -> None:
    plot_df = corr.dropna(subset=["spearman_vs_fair_pay_score"]).copy()
    if plot_df.empty:
        return
    plot_df = plot_df.sort_values("spearman_vs_fair_pay_score")
    fig, ax = plt.subplots(figsize=(8, max(3.5, 0.4 * len(plot_df))))
    colors = ["#c44e52" if v < 0 else "#4c72b0" for v in plot_df["spearman_vs_fair_pay_score"]]
    y_pos = range(len(plot_df))
    ax.barh(list(y_pos), plot_df["spearman_vs_fair_pay_score"].values, color=colors)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(
        [str(row.label) for _, row in plot_df.iterrows()],
        fontsize=9,
    )
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Spearman rho vs fair_pay_score")
    ax.set_title("Factor correlation with Fair Pay score")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_factor_relationship(df: pd.DataFrame, factor: str, label: str, out_path: Path) -> None:
    series = df[factor]
    n_unique = series.dropna().nunique()
    fig, ax = plt.subplots(figsize=(7, 4))

    # Ordinal / low-cardinality → pass rate by level; else scatter vs wage.
    if n_unique <= 8 and pd.api.types.is_numeric_dtype(series):
        levels = sorted(series.dropna().unique())
        rates = []
        ns = []
        for lv in levels:
            sub = df.loc[series == lv, "fair_pay_score"]
            rates.append(float(sub.mean()) if len(sub) else float("nan"))
            ns.append(len(sub))
        ax.bar([str(lv) for lv in levels], rates, color="#4c72b0")
        for i, (r, n) in enumerate(zip(rates, ns)):
            if pd.notna(r):
                ax.text(i, r + 0.02, f"n={n}", ha="center", va="bottom", fontsize=9)
        ax.set_ylim(0, 1.15)
        ax.set_ylabel("Fair Pay pass rate")
        ax.set_xlabel(label)
        ax.set_title(f"Top factor: {label} vs Fair Pay pass rate (n={len(df)})")
    else:
        plot = df[[factor, "hourly_avg_eur", "fair_pay_score"]].dropna()
        colors = plot["fair_pay_score"].map({0: "#c44e52", 1: "#4c72b0"})
        ax.scatter(plot[factor], plot["hourly_avg_eur"], c=colors, alpha=0.8, edgecolors="white")
        ax.axhline(FAIR_PAY_THRESHOLD_EUR, color="red", linestyle="--", linewidth=1, label="threshold 13.9")
        ax.set_xlabel(label)
        ax.set_ylabel("hourly_avg_eur")
        ax.set_title(f"Top factor: {label} vs hourly avg (n={len(plot)})")
        ax.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _zh_label(factor: str, en_label: str) -> str:
    return FACTOR_LABEL_ZH.get(factor, en_label)


def _write_conclusion(df: pd.DataFrame, corr: pd.DataFrame, top: pd.DataFrame, out_path: Path) -> None:
    n = len(df)
    passed = int(df["fair_pay_score"].sum())
    pass_rate = passed / n if n else 0.0
    median = float(df["hourly_avg_eur"].median()) if n else float("nan")
    mean = float(df["hourly_avg_eur"].mean()) if n else float("nan")

    lines = [
        "# Fair Pay 分析结论",
        "",
        f"- 分析样本数 n = {n}",
        f"- 通过数（score=1）= {passed}，通过率 = {pass_rate:.1%}",
        f"- 平均时薪（hourly_avg_eur）中位数 = {median:.2f}，均值 = {mean:.2f}",
        f"- 阈值 = {FAIR_PAY_THRESHOLD_EUR} EUR/h",
        "",
        "## 影响因素相关性（Spearman）",
        "- 目标：`fair_pay_score`；同步给出与 `hourly_avg_eur` 的相关系数。",
        "- 未纳入与得分定义直接循环的变量（如时薪本身）。",
        "",
    ]
    if corr.empty:
        lines.append("- 无可用因子。")
    else:
        for _, row in corr.iterrows():
            rho_s = row["spearman_vs_fair_pay_score"]
            rho_w = row["spearman_vs_hourly_avg_eur"]
            rho_s_txt = f"{rho_s:.3f}" if pd.notna(rho_s) else "nan"
            rho_w_txt = f"{rho_w:.3f}" if pd.notna(rho_w) else "nan"
            zh = _zh_label(str(row["factor"]), str(row["label"]))
            lines.append(
                f"- {zh} (`{row['factor']}`): "
                f"ρ_score={rho_s_txt} (n={int(row['n_vs_score'])}), "
                f"ρ_wage={rho_w_txt} (n={int(row['n_vs_wage'])})"
            )

    lines.append("")
    lines.append("## 最具影响力的因子")
    if top.empty:
        lines.append("- 未能选出有效因子（样本过小或方差不足）。")
    else:
        for i, (_, row) in enumerate(top.iterrows(), start=1):
            rho_s = row["spearman_vs_fair_pay_score"]
            rho_s_txt = f"{rho_s:.3f}" if pd.notna(rho_s) else "nan"
            zh = _zh_label(str(row["factor"]), str(row["label"]))
            lines.append(
                f"- Top{i}: {zh} (`{row['factor']}`), |ρ|={row['abs_spearman_vs_score']:.3f}, ρ={rho_s_txt}"
            )
        lines.append("- 关系图见 `top_factor_*_vs_score.png`。")

    lines.extend(
        [
            "",
            "## 局限",
            "- 仅 hourly；未估计 fixed；未扣工作相关成本；n 较小，相关≠因果，结论仅描述本样本。",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def run(df: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    """Score hourly jobs; write csv/plots/结论.md; return fair_pay_df."""
    out = _ensure_out_dir(out_dir)

    required = {"type", "budget_min_eur", "budget_max_eur"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input missing columns (run add_eur_columns first): {missing}")

    fair = df[df["type"] == "hourly"].copy()
    fair = fair.dropna(subset=["budget_min_eur", "budget_max_eur"])

    fair["hourly_min_eur"] = fair["budget_min_eur"]
    fair["hourly_max_eur"] = fair["budget_max_eur"]
    fair["hourly_avg_eur"] = (fair["hourly_min_eur"] + fair["hourly_max_eur"]) / 2
    fair["fair_pay_score"] = (fair["hourly_avg_eur"] >= FAIR_PAY_THRESHOLD_EUR).astype(int)

    export = fair[[c for c in EXPORT_COLS if c in fair.columns]].copy()
    export.to_csv(out / "fair_pay_hourly.csv", index=False, encoding="utf-8-sig")

    _plot_score_distribution(fair, out / "score_distribution.png")
    _plot_hourly_avg_boxplot(fair, out / "hourly_avg_boxplot.png")

    # Remove obsolete outputs from earlier runs.
    for obsolete_name in ("pass_rate_by_category.png",):
        obsolete = out / obsolete_name
        if obsolete.exists():
            obsolete.unlink()
    for stale in out.glob("top_factor_*_vs_score.png"):
        stale.unlink()

    factor_df = _prepare_factor_frame(fair)
    corr = _compute_correlations(factor_df)
    if not corr.empty:
        corr.to_csv(out / "factor_correlation.csv", index=False, encoding="utf-8-sig")
        _plot_factor_correlation(corr, out / "factor_correlation.png")
        top = corr.dropna(subset=["abs_spearman_vs_score"]).head(TOP_N_FACTORS)
        for i, (_, row) in enumerate(top.iterrows(), start=1):
            _plot_factor_relationship(
                factor_df,
                str(row["factor"]),
                str(row["label"]),
                out / f"top_factor_{i}_{row['factor']}_vs_score.png",
            )
    else:
        top = corr

    _write_conclusion(fair, corr, top if isinstance(top, pd.DataFrame) else corr, out / "结论.md")
    return fair
