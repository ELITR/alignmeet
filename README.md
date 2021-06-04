# Minuting annotation tool

## Requirements

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Execution

```
source venv/bin/activate
python3 run.py
```

## File specification

### alignment

Supported locations:
- `./annotations/transcript+minutes`
- `./alignment+transcript+minutes`

Line format:
```
trascript_line minutes_line problem_index
```

Columns `minutes_line` and `problem_index` could be `None` in some cases.
