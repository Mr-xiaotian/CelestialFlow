# persistence Test Package

> 📅 Last Updated: 2026/06/18

## Purpose
`tests/persistence/` covers three persistence paths (error fallback, log recording, and sqlite utility functions), verifying that Inlet/Spout paired components can correctly write to disk or batch-flush logs in background threads.

> ⚠️ **Changed**: The persistence layer has migrated from JSONL format to sqlite. Old files `test_fail.py`, `test_jsonl.py`, `test_success.py` have been replaced by `test_fallback.py` and `test_splite.py`.

## Included Test Files
- `test_fallback.py`: Error and success result sqlite persistence (`FallbackInlet` / `FallbackSpout`).
- `test_log.py`: Log record batch writing to text files (`LogInlet` / `LogSpout`).
- `test_splite.py`: sqlite utility functions (table creation, CRUD, state transitions, grouped reads).

## How to Run

```bash
pytest tests/persistence -v
pytest tests/persistence -k "fallback or log or splite" -v
```

## Deprecated Documents

| Document | Description |
|------|------|
| `test_fail.md` | Old JSONL error persistence → merged into `test_fallback.md` |
| `test_jsonl.md` | Old JSONL utility functions → replaced by `test_splite.md` |
| `test_success.md` | Old success result caching → merged into `test_fallback.md` |
