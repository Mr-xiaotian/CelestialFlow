from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from celestialflow.persistence.core_fallback import FallbackSpout
from celestialflow.persistence.core_log import LogSpout
from celestialflow.persistence.util_sqlite import connect_db


class BenchLogSpout(LogSpout):
    def __init__(self, base_dir: Path) -> None:
        super().__init__()
        self._base_dir = base_dir

    def _before_start(self) -> None:
        self.log_path = self._base_dir / "bench_task_logger.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.log_path.open("a", encoding="utf-8")


class BenchFallbackSpout(FallbackSpout):
    def __init__(self, base_dir: Path, error_source: str = "bench_fallback") -> None:
        super().__init__(error_source)
        self._base_dir = base_dir

    def _before_start(self) -> None:
        self.db_path = self._base_dir / "bench_fallback.sqlite3"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = connect_db(self.db_path)


def build_log_records(count: int) -> list[dict[str, Any]]:
    return [
        {
            "timestamp": "2026-06-17 12:00:00",
            "level": "INFO",
            "message": f"bench log line {i}",
        }
        for i in range(count)
    ]


def build_fallback_insert_records(count: int) -> list[dict[str, Any]]:
    return [
        {
            "__op__": "insert",
            "record": {
                "event_id": i,
                "stage": "BenchStage",
                "status": "pending",
                "task_json": i,
            },
        }
        for i in range(count)
    ]


def run_spout_bench(spout: Any, records: list[dict[str, Any]]) -> dict[str, float]:
    queue = spout.get_queue()
    for record in records:
        queue.put(record)

    start = time.perf_counter()
    spout.start()
    spout.stop()
    elapsed = time.perf_counter() - start
    throughput = len(records) / elapsed if elapsed > 0 else float("inf")
    return {
        "count": float(len(records)),
        "elapsed": elapsed,
        "throughput": throughput,
        "us_per_record": (elapsed / len(records)) * 1_000_000 if records else 0.0,
    }


def print_result(name: str, result: dict[str, float]) -> None:
    count = int(result["count"])
    print(f"\n{name}")
    print(f"  records:        {count:,}")
    print(f"  elapsed:        {result['elapsed']:.4f}s")
    print(f"  throughput:     {result['throughput']:,.2f} records/s")
    print(f"  avg per record: {result['us_per_record']:.2f} us")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark LogSpout and FallbackSpout drain throughput."
    )
    parser.add_argument(
        "--log-count",
        type=int,
        default=200_000,
        help="Preloaded log records for LogSpout benchmark.",
    )
    parser.add_argument(
        "--fallback-count",
        type=int,
        default=20_000,
        help="Preloaded fallback insert records for FallbackSpout benchmark.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("Running persistence spout benchmarks...")
    print(f"  log-count:      {args.log_count:,}")
    print(f"  fallback-count: {args.fallback_count:,}")
    print("  model: preload queue -> start spout -> drain all queued records")

    with tempfile.TemporaryDirectory(prefix="cf_bench_log_") as log_dir_str:
        log_spout = BenchLogSpout(Path(log_dir_str))
        log_result = run_spout_bench(log_spout, build_log_records(args.log_count))
        print_result("LogSpout", log_result)

    with tempfile.TemporaryDirectory(prefix="cf_bench_fallback_") as fallback_dir_str:
        fallback_spout = BenchFallbackSpout(Path(fallback_dir_str))
        fallback_result = run_spout_bench(
            fallback_spout,
            build_fallback_insert_records(args.fallback_count),
        )
        print_result("FallbackSpout (insert + commit per changed record)", fallback_result)


if __name__ == "__main__":
    main()
