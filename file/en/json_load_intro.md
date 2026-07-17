# Introduction to `json.load`

`json.load` is a function in Python’s standard-library `json` module. It **reads JSON from a file and converts it into a Python object**.

## Basic usage

```python
import json

with open("rawdata/dataset_xxx.json", "r", encoding="utf-8") as f:
    records = json.load(f)
```

- It takes a **file object** `f` (hence the name `load`)
- It returns a Python data structure, not a string

## JSON → Python type mapping

| JSON | Python |
|------|--------|
| `{}` object | `dict` |
| `[]` array | `list` |
| `"text"` | `str` |
| `123` | `int` |
| `3.14` | `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

## With this project’s data

The JSON files are top-level arrays:

```json
[
  { "id": 40582547, "title": "...", "jobs": [...] },
  { "id": 40577455, "title": "...", "jobs": [...] }
]
```

After `json.load`:

```python
records = [
    {"id": 40582547, "title": "...", "jobs": [...]},
    {"id": 40577455, "title": "...", "jobs": [...]},
]
```

- `records` is a **list**
- Each element is a **dict**
- Then you can pass them to `pd.json_normalize(records)` to flatten into a table

## Difference from `json.loads`

| Function | Input | Use case |
|----------|-------|----------|
| `json.load(f)` | **File object** | Read from a `.json` file |
| `json.loads(s)` | **String** | Already have JSON text, e.g. API response |

```python
# load — from file
with open("data.json") as f:
    data = json.load(f)

# loads — from string (note the trailing s)
text = '{"name": "Alice"}'
data = json.loads(text)
```

## Common caveats

1. **Encoding:** for non-ASCII text, prefer `encoding="utf-8"`
2. **Format:** must be valid JSON; trailing commas, single quotes, etc. will error
3. **Large files:** loads entirely into memory; fine for this project’s datasets
4. **Use `with open`:** closes the file automatically; safer than manual `f.close()`

## Where it appears in project scripts

In `dataset_extact_script.py`:

```python
with path.open(encoding="utf-8") as f:
    records = json.load(f)   # file → Python list[dict]

df = pd.json_normalize(records)  # then to DataFrame
```

Flow: **JSON file → `json.load` → Python object → pandas processing**.

## One-line summary

`json.load` = **open a JSON file, parse it into Python dicts/lists for downstream code.**
