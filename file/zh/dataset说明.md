# 清洗后数据集说明（dataset.csv）

**数据文件：** `dataset/dataset.csv`  
**生成脚本：** `dataset_extact_script.py`  
**原始来源：** `rawdata/dataset_*.json`（Freelancer.com，经 Apify `freelancer-scraper` 抓取）  
**编码：** UTF-8 with BOM（`utf-8-sig`）  
**格式：** CSV，每行一条公开项目（project）

## 概览


| 项    | 说明                                 |
| ---- | ---------------------------------- |
| 记录数  | **162** 条（按 `id` 去重，同 id 保留最后一次抓取） |
| 列数   | **19**                             |
| 国家范围 | 抓取侧限定为 **Germany**，本表不单独保存国家列      |
| 语言范围 | 主要为 `**en`**（120）与 `**de**`（42）    |
| 计价类型 | `fixed` 130 条；`hourly` 32 条        |


**来源文件（`source_file`）：**

- `dataset_freelancer-scraper_2026-06-10_18-23-52-667.json`
- `dataset_freelancer-scraper_2026-07-02_23-54-41-352.json`
- `dataset_freelancer-scraper_2026-07-14_21-45-57-461.json`

> 原始 JSON 字段说明见 `[rawdata说明.md](rawdata说明.md)`。本表是从原始嵌套结构中抽取、摊平后的分析用子集。

---

## 字段说明

### 标识与内容


| 列名            | 类型     | 含义                   | 缺失情况 |
| ------------- | ------ | -------------------- | ---- |
| `id`          | number | Freelancer 项目唯一 ID   | 无    |
| `title`       | string | 项目标题                 | 无    |
| `url`         | string | 项目详情页链接              | 无    |
| `description` | string | 完整项目描述（需求、交付物、技能要求等） | 无    |


### 计价与预算


| 列名                       | 类型     | 含义                                | 缺失情况        |
| ------------------------ | ------ | --------------------------------- | ----------- |
| `type`                   | string | 计价方式：`fixed`（固定总价）或 `hourly`（按小时） | 无           |
| `budget_min`             | number | 预算下限。`fixed` 为总价下限；`hourly` 为时薪下限 | 无           |
| `budget_max`             | number | 预算上限。`fixed` 为总价上限；`hourly` 为时薪上限 | 少量缺失（约 4 条） |
| `currency_code`          | string | ISO 货币代码，如 `EUR`、`USD`、`INR`      | 无           |
| `currency_exchange_rate` | number | 相对 USD 的汇率（USD 为 `1`）             | 无           |


当前货币分布（约）：`EUR` 120、`USD` 36、`INR` 4，以及少量 `AUD`、`SGD`。

### 工时承诺（仅 hourly）

来自原始字段 `hourly_project_info.commitment`。仅 `type = hourly` 的项目有值。


| 列名                    | 类型     | 含义                    | 缺失情况                |
| --------------------- | ------ | --------------------- | ------------------- |
| `commitment_hours`    | number | 预期工时，如 `40`           | `fixed` 项目为空（130 条） |
| `commitment_interval` | string | 工时周期，本数据均为 `week`（每周） | 同上                  |


### 技能 / 类别标签

由原始 `jobs[]` 数组展开拼接（多个值用 `", "` 连接）：


| 列名                   | 类型     | 含义         | 示例                        |
| -------------------- | ------ | ---------- | ------------------------- |
| `job_names`          | string | 技能标签名列表    | `Python, Web Scraping`    |
| `job_category_names` | string | 所属大类名称列表   | `Websites, IT & Software` |
| `job_category_ids`   | string | 所属大类 ID 列表 | `1, 6`                    |


### 投标统计


| 列名          | 类型     | 含义                                   | 缺失情况        |
| ----------- | ------ | ------------------------------------ | ----------- |
| `bid_count` | number | 当前收到的投标数量                            | 少量缺失（约 8 条） |
| `bid_avg`   | number | 所有投标金额的平均值（`fixed` 为总价，`hourly` 为时薪） | 同上          |


### 语言与本地要求


| 列名         | 类型      | 含义                                | 缺失情况                                  |
| ---------- | ------- | --------------------------------- | ------------------------------------- |
| `local`    | boolean | 是否要求本地 / on-site 工作               | 多数为空（抓取时未返回该字段）；有值时为 `True` / `False` |
| `language` | string  | 项目**发帖语言**（如 `en`、`de`），不等于德语能力要求 | 无                                     |


### 溯源


| 列名            | 类型     | 含义                  |
| ------------- | ------ | ------------------- |
| `source_file` | string | 该条记录来自哪个原始 JSON 文件名 |


---

## 与原始 JSON 的字段对应


| CSV 列                    | 原始路径                                      |
| ------------------------ | ----------------------------------------- |
| `id`                     | `id`                                      |
| `title`                  | `title`                                   |
| `url`                    | `url`                                     |
| `description`            | `description`                             |
| `type`                   | `type`                                    |
| `budget_min`             | `budget.minimum`                          |
| `budget_max`             | `budget.maximum`                          |
| `currency_code`          | `currency.code`                           |
| `currency_exchange_rate` | `currency.exchange_rate`                  |
| `commitment_hours`       | `hourly_project_info.commitment.hours`    |
| `commitment_interval`    | `hourly_project_info.commitment.interval` |
| `job_names`              | `jobs[].name`（拼接）                         |
| `job_category_names`     | `jobs[].category.name`（拼接）                |
| `job_category_ids`       | `jobs[].category.id`（拼接）                  |
| `bid_count`              | `bid_stats.bid_count`                     |
| `bid_avg`                | `bid_stats.bid_avg`                       |
| `local`                  | `local`                                   |
| `language`               | `language`                                |
| `source_file`            | （脚本写入，非原始字段）                              |


**未采集：** 国家（`location.country.name`）——因数据集默认限定 Germany。

---

## 与本项目分析的关联


| 分析目标        | 主要列                                                                                                                                      |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Fair Pay 评分 | `type`、`budget_min`、`budget_max`、`currency_code`、`currency_exchange_rate`、`commitment_hours`、`commitment_interval`、`local`、`description` |
| 德语水平编码      | `description`、`title`、`language`、`job_names`                                                                                             |
| 议价能力（项目级）   | `bid_count`、`bid_avg`、`budget_max`                                                                                                       |


**常用衍生指标：**

- `bid_ratio = bid_avg / budget_max`（报价相对预算上限的比例）
- 时薪估算：对 `fixed` 项目需从 `description` 推断工时后再换算；可用 `currency_exchange_rate` 统一到 USD 或 EUR

---

## 数据局限

本表**不包含**：

- 单个投标（bid）明细（报价人、金额、时间）
- 雇主（buyer）信息
- 实际成交金额与中标者
- 平台手续费与付款记录
- 项目完成后的评价 / 评分
- 精确地理位置（国家列未采集；`local` 大量为空）

因此，议价能力分析只能在**项目级**进行。

---

## 如何重新生成

在项目根目录运行：

```bash
python dataset_extact_script.py
```

输出会**覆盖**写入 `dataset/dataset.csv`。