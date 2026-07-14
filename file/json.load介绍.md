# json.load 介绍

`json.load` 是 Python 标准库 `json` 里的函数，用来**从文件里读取 JSON，并转成 Python 对象**。

## 基本用法

```python
import json

with open("rawdata/dataset_xxx.json", "r", encoding="utf-8") as f:
    records = json.load(f)
```

- 读的是**文件对象** `f`（所以叫 `load`）
- 返回的是 Python 数据结构，不是字符串

## JSON → Python 类型对应

| JSON | Python |
|------|--------|
| `{}` 对象 | `dict` 字典 |
| `[]` 数组 | `list` 列表 |
| `"text"` | `str` 字符串 |
| `123` | `int` 整数 |
| `3.14` | `float` 浮点数 |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

## 结合本项目数据

JSON 文件顶层是数组：

```json
[
  { "id": 40582547, "title": "...", "jobs": [...] },
  { "id": 40577455, "title": "...", "jobs": [...] }
]
```

`json.load` 之后得到：

```python
records = [
    {"id": 40582547, "title": "...", "jobs": [...]},
    {"id": 40577455, "title": "...", "jobs": [...]},
]
```

- `records` 是 **list**
- 每个元素是 **dict**
- 之后才能交给 `pd.json_normalize(records)` 摊平成表

## 和 `json.loads` 的区别

| 函数 | 输入 | 场景 |
|------|------|------|
| `json.load(f)` | **文件对象** | 从 `.json` 文件读取 |
| `json.loads(s)` | **字符串** | 已有 JSON 文本，如 API 返回 |

```python
# load — 从文件
with open("data.json") as f:
    data = json.load(f)

# loads — 从字符串（注意有个 s）
text = '{"name": "Alice"}'
data = json.loads(text)
```

## 常见注意点

1. **编码**：中文等非 ASCII 建议 `encoding="utf-8"`
2. **文件格式**：必须是合法 JSON；末尾多逗号、单引号等会报错
3. **大文件**：会一次性读入内存；本项目的几个数据集文件这样用没问题
4. **用 `with open`**：自动关闭文件，比手动 `f.close()` 更安全

## 在本项目脚本里的位置

`dataset_extact_script.py` 中的用法：

```python
with path.open(encoding="utf-8") as f:
    records = json.load(f)   # 文件 → Python list[dict]

df = pd.json_normalize(records)  # 再转成 DataFrame
```

流程是：**JSON 文件 → `json.load` → Python 对象 → pandas 处理**。

## 一句话总结

`json.load` = **打开 JSON 文件，解析成 Python 的 dict / list，方便后续代码使用。**
