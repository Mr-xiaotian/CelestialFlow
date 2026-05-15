# demo_graph.py Demo Documentation

> 📅 Last Updated: 2026/05/15

## Purpose

Demonstrates advanced graph topology construction with `TaskGraph` in CelestialFlow: fan-out/fan-in ETL pipelines, and async staged pipelines.

## Demo Scenarios

### `demo_etl_fan_out_fan_in`
ETL pipeline with fan-out/fan-in topology:

```
Extract ──┬── Normalize ──┬── Load
          └── Enrich ─────┘
```

- `Extract` → Generates records by ID (thread mode, 4 workers)
- `Normalize` → Normalizes record values (thread mode, 4 workers)
- `Enrich` → Adds category labels to records (thread mode, 4 workers)
- `Load` → Saves records (serial mode)

**Graph structure**: DAG, one-to-many fan-out + many-to-one fan-in
**Scheduling mode**: `eager`
**Post-execution**: Calls `graph.get_graph_summary()` to output success/failure task counts

### `demo_async_staged_pipeline`
Two-stage async pipeline:

```
AsyncDouble ──> AsyncToStr
```

- `AsyncDouble` → Asynchronously doubles the input (async mode, 8 workers)
- `AsyncToStr` → Asynchronously converts the result to a string (async mode, 8 workers)

**Graph structure**: DAG, linear two-stage
**Scheduling mode**: `staged` (layer-by-layer execution)
**Post-execution**: Calls `graph.get_status_dict()` to output success/failure task counts per stage

## Key Configuration

- All stages use `stage_mode="thread"`
- ETL pipeline uses `schedule_mode="eager"`, async pipeline uses `schedule_mode="staged"`
- `execution_mode="async"` is used for coroutine task functions

## Potential Issues

1. **No assertions**: Demo script, does not verify result correctness.
2. **ETL functions contain sleep**: `extract_record` (0.5s), `transform_normalize`/`transform_enrich` (0.3s), `load_record` (0.2s); full execution takes some time.

## How to Run

```bash
python demo/demo_graph.py
```

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskStage`)
- `demo_utils` (`extract_record`, `transform_normalize`, `transform_enrich`, `load_record`, `async_double`, `async_to_str`)
- `python-dotenv`
- External services: CelestialTree (optional), Reporter (optional)
