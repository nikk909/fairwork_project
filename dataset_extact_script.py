import pandas as pd
import numpy as np

import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path("rawdata")
OUTPUT_DIR = Path("dataset")
OUTPUT_FILE = OUTPUT_DIR / "dataset.csv"

# 原本列名映射到新的更简洁的列名
FIELD_MAP = {
    "id": "id",
    "title": "title",
    "url": "url",
    "description": "description",
    "type": "type",
    "budget.minimum": "budget_min",
    "budget.maximum": "budget_max",
    "currency.code": "currency_code",
    "currency.exchange_rate": "currency_exchange_rate",
    "hourly_project_info.commitment.hours": "commitment_hours",
    "hourly_project_info.commitment.interval": "commitment_interval",
    "bid_stats.bid_count": "bid_count",
    "bid_stats.bid_avg": "bid_avg",
    "local": "local",
    "location.country.name": "location_country",
    "language": "language",
}


def extract_jobs_fields(jobs):
    """把 jobs 数组里的 name / category 提取并拼成字符串"""
    if not isinstance(jobs, list):
        return pd.Series({
            "job_names": None,
            "job_category_names": None,
            "job_category_ids": None,
        })

    names = []
    category_names = []
    category_ids = []

    for job in jobs:
        if not isinstance(job, dict):
            continue
        if "name" in job:
            names.append(job["name"])
        category = job.get("category", {})
        if isinstance(category, dict):
            if "name" in category:
                category_names.append(category["name"])
            if "id" in category:
                category_ids.append(str(category["id"]))

    return pd.Series({
        "job_names": ", ".join(names) if names else None,
        "job_category_names": ", ".join(category_names) if category_names else None,
        "job_category_ids": ", ".join(category_ids) if category_ids else None,
    })


def load_one_file(path: Path) -> pd.DataFrame:
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    df = pd.json_normalize(records)
    df["source_file"] = path.name

    # 提取 jobs 字段
    jobs_df = df["jobs"].apply(extract_jobs_fields) if "jobs" in df.columns else pd.DataFrame()
    if not jobs_df.empty:
        df = pd.concat([df, jobs_df], axis=1)

    # 只保留需要的列（缺失的列自动补 NaN）
    selected = {}
    for src_col, dst_col in FIELD_MAP.items():
        selected[dst_col] = df[src_col] if src_col in df.columns else pd.NA

    result = pd.DataFrame(selected)
    result["source_file"] = df["source_file"]
    return result


def load_all_datasets(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    files = sorted(data_dir.glob("dataset_*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files found in {data_dir}")

    frames = [load_one_file(path) for path in files]
    combined = pd.concat(frames, ignore_index=True)

    # 同一 id 可能在多个文件里出现，保留最后一次抓取
    combined = combined.drop_duplicates(subset=["id"], keep="last")

    return combined


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    df = load_all_datasets()

    # 列顺序
    columns = [
        "id", "title", "url", "description", "type",
        "budget_min", "budget_max",
        "currency_code", "currency_exchange_rate",
        "commitment_hours", "commitment_interval",
        "job_names", "job_category_names", "job_category_ids",
        "bid_count", "bid_avg", "bid_ratio",
        "local", "location_country", "language",
        "source_file",
    ]
    df = df[columns]

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"Loaded {len(df)} unique projects")
    print(f"Saved to {OUTPUT_FILE}")
    print(df.head())
    print(df.info())


if __name__ == "__main__":
    main()