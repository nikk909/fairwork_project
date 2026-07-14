# Freelancer.com 数据集字段说明

**数据文件：** `data/dataset_freelancer-scraper_2026-06-10_18-23-52-667.json`  
**数据来源：** [Freelancer.com](https://www.freelancer.com/)  
**抓取工具：** Apify `freelancer-scraper`

## 数据结构概览

文件为 JSON **数组**，每个元素代表一条**公开项目（project）**记录。本文件共 **57** 条项目。

> **注意：** API 返回的字段并不完整——仅包含有值的字段；未购买的升级项、空对象等会被省略。不同记录之间的字段可能不一致。

---

## 一、顶层字段

### 标识与内容

| 字段 | 类型 | 含义 |
|------|------|------|
| `id` | number | 项目在 Freelancer 平台上的唯一 ID |
| `title` | string | 项目标题 |
| `url` | string | 项目详情页链接 |
| `description` | string | 完整项目描述（需求、交付物、技能要求等） |
| `preview_description` | string | 描述截断预览（列表页展示用，通常约 100 字符） |

### 项目类型与预算

| 字段 | 类型 | 含义 |
|------|------|------|
| `type` | string | 计价方式：`fixed`（固定总价）或 `hourly`（按小时计费） |
| `budget` | object | 预算范围，见 [budget](#budget) |
| `currency` | object | 货币信息，见 [currency](#currency) |
| `hourly_project_info` | object | **仅 `hourly` 项目**出现；工时承诺与工期，见 [hourly_project_info](#hourly_project_info) |

### 投标统计

| 字段 | 类型 | 含义 |
|------|------|------|
| `bid_stats` | object | 投标汇总统计，见 [bid_stats](#bid_stats) |
| `bidperiod` | number | 竞标开放天数（本数据集均为 `7`） |
| `hidebids` | boolean | 是否对自由职业者隐藏其他投标金额 |
| `time_free_bids_expire` | string | 免费投标窗口截止时间（ISO 8601 UTC） |

### 状态与时间

| 字段 | 类型 | 含义 |
|------|------|------|
| `status` | string | 后端状态（本数据集均为 `active`） |
| `frontend_project_status` | string | 前端展示状态（本数据集均为 `open`，即开放投标） |
| `submitdate` | string | 项目提交日期（UTC） |
| `time_submitted` | string | 项目提交时间（UTC） |
| `time_updated` | string | 最后更新时间（UTC） |
| `deleted` | boolean | 项目是否已删除 |

### 语言与地点

| 字段 | 类型 | 含义 |
|------|------|------|
| `language` | string | 项目发布语言，如 `en`、`de`。注意：这是发帖语言，不等于德语能力要求 |
| `local` | boolean | 是否要求本地/on-site 工作；`true` 时通常有具体 `location` |
| `location` | object | 地理位置，见 [location](#location) |

### 技能标签

| 字段 | 类型 | 含义 |
|------|------|------|
| `jobs` | array | 项目关联的技能/类别标签列表，见 [jobs[]](#jobs) |

### 平台功能与付费升级

| 字段 | 类型 | 含义 |
|------|------|------|
| `upgrades` | object | 雇主购买的付费升级项，见 [upgrades](#upgrades) |
| `featured` | boolean | 是否置顶/Featured 展示 |
| `urgent` | boolean | 是否标记为紧急项目 |
| `assisted` | boolean | 是否使用 Freelancer 协助/招聘专员服务 |
| `hireme` | boolean | 是否为 Hire Me 直聘模式 |
| `nonpublic` | boolean | 是否为非公开项目 |
| `active_prepaid_milestone` | object | 预付里程碑信息（多为空对象 `{}`） |

### 企业与合规

| 字段 | 类型 | 含义 |
|------|------|------|
| `enterprise_ids` | array | 关联企业账户 ID（通常为空） |
| `enterprises` | array | 企业详情（通常为空） |
| `group_ids` | array | 用户组 ID（通常为空） |
| `pool_ids` | array | 人才池 ID；本数据集多为 `[1]`（公开池） |
| `is_buyer_kyc_required` | boolean | 雇主是否需完成 KYC 身份验证 |
| `is_seller_kyc_required` | boolean | 自由职业者是否需完成 KYC 身份验证 |
| `is_escrow_project` | boolean | 是否通过平台 escrow 托管支付 |

---

## 二、嵌套对象字段

### budget

| 字段 | 类型 | 含义 |
|------|------|------|
| `minimum` | number | 预算下限。`fixed` 为总价下限；`hourly` 为时薪下限 |
| `maximum` | number | 预算上限。`fixed` 为总价上限；`hourly` 为时薪上限 |

### bid_stats

| 字段 | 类型 | 含义 |
|------|------|------|
| `bid_count` | number | 当前收到的投标数量 |
| `bid_avg` | number | 所有投标金额的平均值（`fixed` 为总价，`hourly` 为时薪） |

### currency

| 字段 | 类型 | 含义 |
|------|------|------|
| `id` | number | Freelancer 内部货币 ID |
| `code` | string | ISO 货币代码，如 `EUR`、`USD`、`INR`、`AUD` |
| `name` | string | 货币名称，如 `Euro` |
| `sign` | string | 货币符号，如 `€`、`$`、`₹` |
| `country` | string | 关联地区代码，如 `EU`、`US`、`IN` |
| `exchange_rate` | number | 相对 USD 的汇率（USD 为 `1`） |
| `is_escrowcom_supported` | boolean | 是否支持 Escrow.com 托管 |
| `is_external` | boolean | 是否为外部/非平台标准货币（仅部分记录有） |

### hourly_project_info

仅 `type: "hourly"` 的项目出现。

| 字段 | 类型 | 含义 |
|------|------|------|
| `commitment.hours` | number | 预期工时，如 `40` |
| `commitment.interval` | string | 工时周期，如 `week`（每周） |
| `duration_enum` | string | 项目工期枚举；本数据集均为 `unspecified`（未指定） |

### location

| 字段 | 类型 | 含义 |
|------|------|------|
| `country` | object | 国家信息；无具体位置时为 `{}`，有值时含 `name` 字段 |
| `country.name` | string | 国家名称，如 `Saudi Arabia` |
| `administrative_area` | string | 省/州，如 `Eastern Province` |
| `vicinity` | string | 城市/附近区域，如 `Dhahran` |
| `latitude` | number | 纬度 |
| `longitude` | number | 经度 |
| `timezone` | object | 时区信息（本数据集多为空 `{}`） |

### jobs[]

`jobs` 数组中每个元素代表一个技能/类别标签。

| 字段 | 类型 | 含义 |
|------|------|------|
| `id` | number | 技能标签 ID |
| `name` | string | 技能名称，如 `Python`、`German Translator` |
| `seo_url` | string | URL 路径片段，如 `web_scraping` |
| `local` | boolean | 该技能是否标记为本地需求（可选） |
| `category.id` | number | 所属大类 ID |
| `category.name` | string | 所属大类名称，如 `Websites, IT & Software` |

### upgrades

雇主为项目购买的付费升级项。多数记录只列出值为 `true` 的项；部分记录（如第一条）列出全部布尔字段。

| 字段 | 含义 |
|------|------|
| `listed` | 已公开发布（几乎所有项目为 `true`） |
| `assisted` | 平台协助/招聘专员服务 |
| `recruiter` | 招聘专员协助 |
| `pf_only` | Preferred Freelancer Only（仅优选自由职业者可投标） |
| `ip_contract` | 含知识产权（IP）合同条款 |
| `NDA` | 保密协议（Non-Disclosure Agreement） |
| `sealed` | 密封投标（投标人看不到他人报价） |
| `featured` | 置顶展示 |
| `urgent` | 紧急标记 |
| `premium` | Premium 项目 |
| `fulltime` | 全职性质 |
| `qualified` | 限定认证/合格自由职业者 |
| `enterprise` | 企业级项目 |
| `nonpublic` | 非公开 |
| `non_compete` | 竞业限制条款 |
| `project_management` | 含项目管理服务 |
| `active_prepaid_milestone` | 预付里程碑（嵌套对象） |

---

## 三、与本项目分析的关联

| 分析目标 | 主要字段 |
|----------|----------|
| Fair Pay 评分 | `type`、`budget`、`currency`、`hourly_project_info`、`local`、`location`、`description` |
| 德语水平编码 | `description`、`title`、`language`、`jobs[].name` |
| 议价能力（项目级） | `bid_stats.bid_count`、`bid_stats.bid_avg`、`budget.maximum` |

**常用衍生指标：**

- `bid_ratio = bid_stats.bid_avg / budget.maximum`（报价相对预算上限的比例）
- 时薪估算：对 `fixed` 项目需从 `description` 推断工时后再换算

---

## 四、数据局限

本数据集**不包含**以下信息：

- 单个投标（bid）明细（报价人、报价金额、投标时间）
- 雇主（buyer）信息
- 实际成交金额与中标的自由职业者
- 平台手续费与付款记录
- 项目完成后的评价/评分

因此，议价能力分析只能在**项目级**进行，无法直接分析个体投标人的议价行为。
