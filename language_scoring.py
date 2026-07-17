"""Topic 2: language requirement scoring + vs Fair Pay analysis."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是德国 Freelancer 岗位语言要求标注助手。根据岗位文本推断德语与英语要求水平，只输出一个 JSON 对象，不要 markdown 代码块，不要其他解释。

输出格式（字段名固定）：
{"de_level":<0-3>,"en_level":<1-3>,"de_reason":"<短理由>","en_reason":"<短理由>"}

德语 de_level：
0 = 不需要德语
1 = 基础德语 A1/A2
2 = 流畅德语 B1/B2
3 = 必须良好德语 C1/C2

英语 en_level：
1 = 入门 A1/A2
2 = 流畅 B1/B2
3 = 精通 C1/C2

规则：
1. 只依据给定文本判断，不要编造文本未支持的要求。
2. 若出现多个水平，只取最低要求水平。
3. 无法确定时偏向更低水平。
4. de_reason / en_reason 必须中英双语，格式固定为「中文说明 / English explanation」，两侧合计尽量简短（约各不超过 30 词）。
5. 若文本未提及德语要求，可判 de_level=0，并在理由中说明「未发现德语要求 / No German requirement found」。
6. 若文本未体现更高英语要求，可判 en_level=1，并说明「默认英语入门 / Default English beginner」。

You are a language-requirement annotator for Freelancer jobs targeting Germany.
Infer German and English requirements from the job text. Output ONE JSON object only — no markdown fences, no extra text.

Output schema (fixed keys):
{"de_level":<0-3>,"en_level":<1-3>,"de_reason":"<short>","en_reason":"<short>"}

de_level: 0=none, 1=A1/A2 basic, 2=B1/B2 fluent, 3=C1/C2 strong required
en_level: 1=A1/A2 beginner, 2=B1/B2 fluent, 3=C1/C2 proficient

Rules: use only the given text; if multiple levels appear take the lowest; when unsure prefer lower.
Each reason MUST be bilingual in the form "中文 / English".
If no German requirement appears, de_level may be 0 with that explained bilingually.
If no higher English requirement appears, en_level may be 1 (default beginner) with that explained bilingually."""

# phrase (lowercase) -> (lang, level); longer phrases should be checked first
VOCAB: list[tuple[str, str, int]] = [
    ("german not required", "de", 0),
    ("no german required", "de", 0),
    ("no german", "de", 0),
    ("german optional", "de", 0),
    ("nicht erforderlich", "de", 0),
    ("kein deutsch", "de", 0),
    ("basic german", "de", 1),
    ("einfaches deutsch", "de", 1),
    ("anfänger deutsch", "de", 1),
    ("fluent german", "de", 2),
    ("gutes deutsch", "de", 2),
    ("good german", "de", 2),
    ("native german", "de", 3),
    ("muttersprachler", "de", 3),
    ("verhandlungssicher", "de", 3),
    ("business german", "de", 3),
    ("basic english", "en", 1),
    ("einfaches englisch", "en", 1),
    ("fluent english", "en", 2),
    ("gutes englisch", "en", 2),
    ("good english", "en", 2),
    ("business english", "en", 2),
    ("native english", "en", 3),
    ("muttersprachliches englisch", "en", 3),
]

CEFR_RE = re.compile(r"\b(A1|A2|B1|B2|C1|C2)\b", re.IGNORECASE)
CEFR_MAP = {"A1": 1, "A2": 1, "B1": 2, "B2": 2, "C1": 3, "C2": 3}
# Word boundaries avoid matching "Germany" as German language requirement.
DE_CTX = re.compile(r"(?<![a-z])(german|deutsch|德语)(?![a-z])", re.IGNORECASE)
EN_CTX = re.compile(r"(?<![a-z])(english|englisch|英语)(?![a-z])", re.IGNORECASE)

LANGUAGE_ALL_COLS = [
    "id",
    "title",
    "language",
    "type",
    "job_names",
    "job_category_names",
    "de_level",
    "en_level",
    "de_reason",
    "en_reason",
    "url",
]


def _ensure_out_dir(out_dir: str | Path) -> Path:
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _min_level(current: int | None, new: int) -> int:
    if current is None:
        return new
    return min(current, new)


def _rule_score_row(row: pd.Series) -> tuple[int | None, int | None, str, str]:
    title = str(row.get("title") or "")
    job_names = str(row.get("job_names") or "")
    description = str(row.get("description") or "")
    blob = f"{title} {job_names} {description}"
    blob_l = blob.lower()

    de_level: int | None = None
    en_level: int | None = None
    de_hits: list[str] = []
    en_hits: list[str] = []

    # Vocabulary (longest phrases first — already ordered)
    for phrase, lang, level in VOCAB:
        if phrase in blob_l:
            if lang == "de":
                de_level = _min_level(de_level, level)
                de_hits.append(phrase)
            else:
                en_level = _min_level(en_level, level)
                en_hits.append(phrase)

    # CEFR near language context (±40 chars)
    for m in CEFR_RE.finditer(blob):
        level = CEFR_MAP[m.group(1).upper()]
        start = max(0, m.start() - 40)
        end = min(len(blob), m.end() + 40)
        window = blob[start:end]
        has_de = bool(DE_CTX.search(window))
        has_en = bool(EN_CTX.search(window))
        if has_de and not has_en:
            de_level = _min_level(de_level, level)
            de_hits.append(m.group(1))
        elif has_en and not has_de:
            en_level = _min_level(en_level, level)
            en_hits.append(m.group(1))
        # ambiguous → ignore

    # Skill tags in job_names
    names_l = job_names.lower()
    tags = [t.strip() for t in re.split(r"[,;/|]", names_l) if t.strip()]
    for tag in tags:
        if tag in ("german", "deutsch"):
            de_level = _min_level(de_level, 2)
            de_hits.append(f"tag:{tag}")
        elif tag in ("english", "englisch"):
            en_level = _min_level(en_level, 2)
            en_hits.append(f"tag:{tag}")

    # No soft defaults here: "no German requirement" / "default English beginner"
    # must go through AI-assisted judgment (DeepSeek) so reasons are marked [AI辅助].

    de_reason = (
        f"[rule] 命中规则: {', '.join(de_hits)} / rule hits: {', '.join(de_hits)}"
        if de_hits
        else ""
    )
    en_reason = (
        f"[rule] 命中规则: {', '.join(en_hits)} / rule hits: {', '.join(en_hits)}"
        if en_hits
        else ""
    )
    return de_level, en_level, de_reason, en_reason


def _build_user_content(row: pd.Series) -> str:
    return (
        "请根据以下岗位信息判断语言要求，并按约定返回 JSON。\n"
        "Judge language requirements from the job below and return JSON as specified.\n\n"
        f"id: {row.get('id', '')}\n"
        f"title: {row.get('title', '')}\n"
        f"language (post language / 发帖语言): {row.get('language', '')}\n"
        f"job_names: {row.get('job_names', '')}\n"
        f"job_category_names: {row.get('job_category_names', '')}\n"
        f"description:\n{row.get('description', '')}"
    )


def _call_deepseek(row: pd.Series) -> dict | None:
    load_dotenv()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        logger.warning("DEEPSEEK_API_KEY missing; skip DeepSeek for id=%s", row.get("id"))
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_content(row)},
            ],
            stream=False,
        )
        content = response.choices[0].message.content or ""
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        data = json.loads(content)
        de = int(data["de_level"])
        en = int(data["en_level"])
        if de not in {0, 1, 2, 3} or en not in {1, 2, 3}:
            raise ValueError(f"invalid levels: de={de}, en={en}")
        return {
            "de_level": de,
            "en_level": en,
            "de_reason": f"[AI辅助] {data.get('de_reason', '')}".strip(),
            "en_reason": f"[AI辅助] {data.get('en_reason', '')}".strip(),
        }
    except Exception as exc:  # noqa: BLE001 — keep pipeline running
        logger.warning("DeepSeek failed for id=%s: %s", row.get("id"), exc)
        return None


def _score_one_row(row: pd.Series) -> dict:
    de_level, en_level, de_reason, en_reason = _rule_score_row(row)

    # Any incomplete side (including former soft defaults) → AI-assisted fill
    if de_level is None or en_level is None:
        api = _call_deepseek(row)
        if api:
            if de_level is None:
                de_level = api["de_level"]
                de_reason = api["de_reason"]
            if en_level is None:
                en_level = api["en_level"]
                en_reason = api["en_reason"]

    # Posting-language floor (after rule / AI)
    lang = str(row.get("language") or "").lower().strip()
    if lang == "en" and en_level is not None:
        en_level = max(en_level, 1)
    elif lang == "en" and en_level is None:
        en_level = 1
        en_reason = (
            "[AI辅助] 发帖语言为英语，暂定英语入门 / "
            "Posting language is English; default English beginner"
        )
    if lang == "de" and de_level is not None:
        de_level = max(de_level, 1)
    elif lang == "de" and de_level is None:
        de_level = 1
        de_reason = (
            "[AI辅助] 发帖语言为德语，暂定基础德语 / "
            "Posting language is German; default basic German"
        )

    if de_level is None:
        de_level = 0
        de_reason = (
            "[fallback] 无法完成AI判定，默认不需要德语 / "
            "AI unavailable; default no German required"
        )
        logger.warning("fallback de_level=0 for id=%s", row.get("id"))
    if en_level is None:
        en_level = 1
        en_reason = (
            "[fallback] 无法完成AI判定，默认英语入门 / "
            "AI unavailable; default English beginner"
        )
        logger.warning("fallback en_level=1 for id=%s", row.get("id"))

    return {
        "de_level": int(de_level),
        "en_level": int(en_level),
        "de_reason": de_reason or "[rule]",
        "en_reason": en_reason or "[rule]",
    }


def score_languages(df: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    """Encode de/en levels for all rows; write language_all.csv."""
    out = _ensure_out_dir(out_dir)
    result = df.copy()
    scored = result.apply(_score_one_row, axis=1, result_type="expand")
    result["de_level"] = scored["de_level"]
    result["en_level"] = scored["en_level"]
    result["de_reason"] = scored["de_reason"]
    result["en_reason"] = scored["en_reason"]

    export = result[[c for c in LANGUAGE_ALL_COLS if c in result.columns]].copy()
    export.to_csv(out / "language_all.csv", index=False, encoding="utf-8-sig")
    return result


def _cross_table(merged: pd.DataFrame, level_col: str) -> pd.DataFrame:
    return (
        merged.groupby(level_col, dropna=False)
        .agg(n=("fair_pay_score", "size"), mean_score=("fair_pay_score", "mean"), pass_rate=("fair_pay_score", "mean"))
        .reset_index()
        .sort_values(level_col)
    )


def _spearman(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    """Spearman ρ via Pearson on ranks (no scipy dependency)."""
    pair = pd.concat([x, y], axis=1).dropna()
    n = len(pair)
    if n < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return float("nan"), n
    return float(pair.iloc[:, 0].rank().corr(pair.iloc[:, 1].rank())), n


def _plot_pass_rate(cross: pd.DataFrame, level_col: str, title: str, out_path: Path) -> None:
    labels = [str(v) for v in cross[level_col]]
    rates = cross["pass_rate"].tolist()
    ns = cross["n"].tolist()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(labels, rates, color="#4c72b0")
    for i, (r, n) in enumerate(zip(rates, ns)):
        ax.text(i, r + 0.02, f"n={int(n)}", ha="center", va="bottom", fontsize=9)
    ax.set_xlabel(level_col)
    ax.set_ylabel("pass rate")
    ax.set_ylim(0, 1.15)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_de_en_score_comparison(
    cross_de: pd.DataFrame,
    cross_en: pd.DataFrame,
    rho_de: float,
    rho_en: float,
    n: int,
    out_path: Path,
) -> None:
    """Third comparison chart: DE vs EN pass-rate panels + ρ annotation."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, cross, level_col, title, rho in [
        (axes[0], cross_de, "de_level", "German requirement (de_level)", rho_de),
        (axes[1], cross_en, "en_level", "English requirement (en_level)", rho_en),
    ]:
        labels = [str(v) for v in cross[level_col]]
        rates = cross["pass_rate"].tolist()
        ns = cross["n"].tolist()
        ax.bar(labels, rates, color="#4c72b0")
        for i, (r, nn) in enumerate(zip(rates, ns)):
            ax.text(i, r + 0.02, f"n={int(nn)}", ha="center", va="bottom", fontsize=8)
        rho_txt = f"{rho:.3f}" if pd.notna(rho) else "nan"
        ax.set_title(f"{title}\nSpearman rho={rho_txt}")
        ax.set_xlabel(level_col)
        ax.set_ylim(0, 1.15)
    axes[0].set_ylabel("Fair Pay pass rate")
    fig.suptitle(f"German vs English x Fair Pay comparison (n={n})", y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def analyze_vs_fair_pay(
    lang_df: pd.DataFrame,
    fair_pay_df: pd.DataFrame,
    out_dir: str | Path,
) -> None:
    """Merge language × Fair Pay; write cross plots and 结论.md."""
    out = _ensure_out_dir(out_dir)
    lang_cols = ["id", "de_level", "en_level"]
    merged = fair_pay_df[["id", "fair_pay_score"]].merge(
        lang_df[lang_cols], on="id", how="inner"
    )
    n = len(merged)

    cross_de = _cross_table(merged, "de_level")
    cross_en = _cross_table(merged, "en_level")
    cross_de.to_csv(out / "cross_de.csv", index=False, encoding="utf-8-sig")
    cross_en.to_csv(out / "cross_en.csv", index=False, encoding="utf-8-sig")

    rho_de, n_de = _spearman(merged["de_level"], merged["fair_pay_score"])
    rho_en, n_en = _spearman(merged["en_level"], merged["fair_pay_score"])
    compare = pd.DataFrame(
        [
            {
                "language": "de",
                "level_col": "de_level",
                "n": n_de,
                "spearman_vs_fair_pay_score": rho_de,
                "abs_spearman": abs(rho_de) if pd.notna(rho_de) else float("nan"),
            },
            {
                "language": "en",
                "level_col": "en_level",
                "n": n_en,
                "spearman_vs_fair_pay_score": rho_en,
                "abs_spearman": abs(rho_en) if pd.notna(rho_en) else float("nan"),
            },
        ]
    )
    compare.to_csv(out / "de_vs_en_comparison.csv", index=False, encoding="utf-8-sig")

    _plot_pass_rate(
        cross_de,
        "de_level",
        f"German requirement level vs Fair Pay pass rate (n={n})",
        out / "de_level_vs_pass_rate.png",
    )
    _plot_pass_rate(
        cross_en,
        "en_level",
        f"English requirement level vs Fair Pay pass rate (n={n})",
        out / "en_level_vs_pass_rate.png",
    )
    _plot_de_en_score_comparison(
        cross_de,
        cross_en,
        rho_de,
        rho_en,
        n,
        out / "de_vs_en_score_comparison.png",
    )

    if pd.isna(rho_de) and pd.isna(rho_en):
        stronger = "无法判断"
    elif pd.notna(rho_de) and (pd.isna(rho_en) or abs(rho_de) >= abs(rho_en)):
        stronger = "德语"
    else:
        stronger = "英语"

    lines = [
        "# 语言 × Fair Pay 结论",
        "",
        f"- 交叉样本 n = {n}（仅已打分 hourly）",
        "",
        "## 对比数值（Spearman ρ vs fair_pay_score）",
        f"- 德语 de_level：ρ = {rho_de:.3f}" if pd.notna(rho_de) else "- 德语 de_level：ρ = nan",
        f"- 英语 en_level：ρ = {rho_en:.3f}" if pd.notna(rho_en) else "- 英语 en_level：ρ = nan",
        f"- |ρ| 更大者：{stronger}（描述性比较，非因果）",
        "",
        "## 德语各 level",
    ]
    for _, row in cross_de.iterrows():
        lines.append(f"- de_level={int(row.de_level)}: n={int(row.n)}, 通过率={row.pass_rate:.1%}")
    lines.append("")
    lines.append("## 英语各 level")
    for _, row in cross_en.iterrows():
        lines.append(f"- en_level={int(row.en_level)}: n={int(row.n)}, 通过率={row.pass_rate:.1%}")
    lines.extend(
        [
            "",
            "## 观察",
            "- 以上为描述性统计，不做因果推断。",
            "- 三张对比图：`de_level_vs_pass_rate.png`、`en_level_vs_pass_rate.png`、`de_vs_en_score_comparison.png`。",
            "",
            "## 局限",
            "- n 小；语言为岗位要求编码，非工人实际能力。",
            "",
        ]
    )
    (out / "结论.md").write_text("\n".join(lines), encoding="utf-8")
