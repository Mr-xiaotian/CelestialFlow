from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RunStats:
    name: str
    seconds: float
    items: int
    throughput: float


def cpu_heavy_transform(value: int, loops: int) -> int:
    acc = value + 1
    for i in range(loops):
        acc = ((acc * 33) ^ (i + value)) % 2_147_483_647
    return acc


def io_heavy_transform(value: int, sleep_s: float) -> int:
    time.sleep(sleep_s)
    return value + 1


def make_cpu_task(loops: int):
    def task(value: int) -> int:
        return cpu_heavy_transform(value, loops)

    return task


def make_io_task(sleep_s: float):
    def task(value: int) -> int:
        return io_heavy_transform(value, sleep_s)

    return task


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def prepare_runtime_root() -> Path:
    project_root = get_project_root()
    os.chdir(project_root)
    return project_root


def build_executor(name: str, func: Any, execution_mode: str, max_workers: int):
    from celestialflow import TaskExecutor

    return TaskExecutor(
        name,
        func,
        execution_mode=execution_mode,
        max_workers=max_workers,
        log_level="CRITICAL",
        persist_result=False,
        enable_duplicate_check=False,
    )


def build_chain_graph(
    name: str,
    funcs: list[Any],
    stage_mode: str,
    execution_mode: str,
    max_workers: int,
):
    from celestialflow import TaskGraph, TaskStage

    stage1 = TaskStage(
        f"{name}_stage_1",
        funcs[0],
        stage_mode=stage_mode,
        execution_mode=execution_mode,
        max_workers=max_workers,
        log_level="CRITICAL",
        persist_result=False,
        enable_duplicate_check=False,
    )
    stage2 = TaskStage(
        f"{name}_stage_2",
        funcs[1],
        stage_mode=stage_mode,
        execution_mode=execution_mode,
        max_workers=max_workers,
        log_level="CRITICAL",
        persist_result=False,
        enable_duplicate_check=False,
    )
    stage3 = TaskStage(
        f"{name}_stage_3",
        funcs[2],
        stage_mode=stage_mode,
        execution_mode=execution_mode,
        max_workers=max_workers,
        log_level="CRITICAL",
        persist_result=False,
        enable_duplicate_check=False,
    )

    graph = TaskGraph(name, schedule_mode="eager", log_level="CRITICAL")
    graph.set_stages([stage1, stage2, stage3])
    graph.connect([stage1], [stage2])
    graph.connect([stage2], [stage3])
    return graph, stage3


def measure_executor(
    name: str,
    execution_mode: str,
    items: list[int],
    workers: int,
    func: Any,
) -> RunStats:
    executor = build_executor(name, func, execution_mode, workers)
    start = time.perf_counter()
    executor.start(items)
    seconds = time.perf_counter() - start
    success_count = executor.metrics.get_success_count()
    if success_count != len(items):
        raise RuntimeError(
            f"{name} success count mismatch: expected {len(items)}, got {success_count}"
        )
    return RunStats(
        name=name,
        seconds=seconds,
        items=len(items),
        throughput=len(items) / seconds if seconds else float("inf"),
    )


def measure_graph(
    name: str,
    stage_mode: str,
    execution_mode: str,
    items: list[int],
    workers: int,
    funcs: list[Any],
) -> RunStats:
    graph, sink_stage = build_chain_graph(name, funcs, stage_mode, execution_mode, workers)
    start = time.perf_counter()
    graph.start_graph({f"{name}_stage_1": items})
    seconds = time.perf_counter() - start
    success_count = sink_stage.metrics.get_success_count()
    if success_count != len(items):
        raise RuntimeError(
            f"{name} success count mismatch: expected {len(items)}, got {success_count}"
        )
    return RunStats(
        name=name,
        seconds=seconds,
        items=len(items),
        throughput=len(items) / seconds if seconds else float("inf"),
    )


def detect_env_name(gil_enabled: bool | None) -> str:
    if gil_enabled is True:
        return "GIL"
    if gil_enabled is False:
        return "No-GIL"
    return "Unknown"


def run_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    project_root = prepare_runtime_root()
    gil_probe = getattr(sys, "_is_gil_enabled", None)
    gil_enabled = bool(gil_probe()) if callable(gil_probe) else None
    cpu_count = os.cpu_count() or 1
    workers = args.workers or min(cpu_count, 16)

    cpu_items = list(range(args.cpu_tasks))
    pipeline_items = list(range(args.pipeline_tasks))
    io_items = list(range(args.io_tasks))

    cpu_task = make_cpu_task(args.cpu_loops)
    pipeline_task = make_cpu_task(args.pipeline_loops)
    io_task = make_io_task(args.io_sleep_ms / 1000.0)

    workload_factories = {
        "executor_cpu_serial": lambda: measure_executor(
            "executor_cpu_serial", "serial", cpu_items, workers, cpu_task
        ),
        "executor_cpu_thread": lambda: measure_executor(
            "executor_cpu_thread", "thread", cpu_items, workers, cpu_task
        ),
        "graph_cpu_pipeline_serial": lambda: measure_graph(
            "graph_cpu_pipeline_serial",
            "serial",
            "serial",
            pipeline_items,
            workers,
            [pipeline_task, pipeline_task, pipeline_task],
        ),
        "graph_cpu_pipeline_thread": lambda: measure_graph(
            "graph_cpu_pipeline_thread",
            "thread",
            "thread",
            pipeline_items,
            workers,
            [pipeline_task, pipeline_task, pipeline_task],
        ),
        "graph_io_pipeline_thread": lambda: measure_graph(
            "graph_io_pipeline_thread",
            "thread",
            "thread",
            io_items,
            workers,
            [io_task, io_task, io_task],
        ),
    }

    repeats: dict[str, list[RunStats]] = {name: [] for name in workload_factories}
    for _ in range(args.repeats):
        for name, factory in workload_factories.items():
            repeats[name].append(factory())

    workloads: dict[str, Any] = {}
    for name, run_stats in repeats.items():
        seconds_values = [item.seconds for item in run_stats]
        throughput_values = [item.throughput for item in run_stats]
        workloads[name] = {
            "mean_seconds": statistics.mean(seconds_values),
            "min_seconds": min(seconds_values),
            "max_seconds": max(seconds_values),
            "stdev_seconds": statistics.stdev(seconds_values)
            if len(seconds_values) > 1
            else 0.0,
            "mean_throughput": statistics.mean(throughput_values),
            "runs": [asdict(item) for item in run_stats],
        }

    return {
        "python": sys.version,
        "python_executable": sys.executable,
        "gil_enabled": gil_enabled,
        "env_name": detect_env_name(gil_enabled),
        "project_root": str(project_root),
        "cpu_count": cpu_count,
        "workers": workers,
        "repeats": args.repeats,
        "parameters": {
            "cpu_tasks": args.cpu_tasks,
            "cpu_loops": args.cpu_loops,
            "pipeline_tasks": args.pipeline_tasks,
            "pipeline_loops": args.pipeline_loops,
            "io_tasks": args.io_tasks,
            "io_sleep_ms": args.io_sleep_ms,
        },
        "workloads": workloads,
    }


def format_seconds(value: float) -> str:
    return f"{value:.4f}s"


def print_summary(payload: dict[str, Any]) -> None:
    gil_status = payload["gil_enabled"]
    if gil_status is None:
        gil_text = "Unknown"
    else:
        gil_text = "Enabled" if gil_status else "Disabled"

    print(f"# CelestialFlow Benchmark ({payload['env_name']})")
    print("")
    print(f"- Python: {payload['python'].splitlines()[0]}")
    print(f"- Executable: {payload['python_executable']}")
    print(f"- GIL: {gil_text}")
    print(f"- Project root: {payload['project_root']}")
    print(f"- Workers: {payload['workers']}")
    print(f"- Repeats: {payload['repeats']}")
    print(
        "- Parameters: "
        f"cpu_tasks={payload['parameters']['cpu_tasks']}, "
        f"cpu_loops={payload['parameters']['cpu_loops']}, "
        f"pipeline_tasks={payload['parameters']['pipeline_tasks']}, "
        f"pipeline_loops={payload['parameters']['pipeline_loops']}, "
        f"io_tasks={payload['parameters']['io_tasks']}, "
        f"io_sleep_ms={payload['parameters']['io_sleep_ms']}"
    )
    print("")
    print("| Workload | Mean | Min | Max | Throughput |")
    print("| :--- | ---: | ---: | ---: | ---: |")
    for workload_name, stats in payload["workloads"].items():
        print(
            "| "
            f"{workload_name} | "
            f"{format_seconds(stats['mean_seconds'])} | "
            f"{format_seconds(stats['min_seconds'])} | "
            f"{format_seconds(stats['max_seconds'])} | "
            f"{stats['mean_throughput']:.2f} items/s |"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark CelestialFlow under the current Python interpreter."
    )
    parser.add_argument("--repeats", type=int, default=3, help="Benchmark repeats per workload")
    parser.add_argument("--workers", type=int, default=0, help="Max workers, 0 means auto")
    parser.add_argument("--cpu-tasks", type=int, default=128)
    parser.add_argument("--cpu-loops", type=int, default=120000)
    parser.add_argument("--pipeline-tasks", type=int, default=96)
    parser.add_argument("--pipeline-loops", type=int, default=60000)
    parser.add_argument("--io-tasks", type=int, default=96)
    parser.add_argument("--io-sleep-ms", type=float, default=10.0)
    parser.add_argument("--json-out", type=Path, default=None, help="Optional JSON output path")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.json_out is not None:
        args.json_out = args.json_out.resolve()

    payload = run_benchmark(args)
    print_summary(payload)

    if args.json_out is not None:
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nJSON written to: {args.json_out}")


if __name__ == "__main__":
    main()
