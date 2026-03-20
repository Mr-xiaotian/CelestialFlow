from __future__ import annotations

import statistics


def summarize(name: str, durations: list[float], count: int) -> None:
    mean_s = statistics.mean(durations)
    std_s = statistics.pstdev(durations) if len(durations) > 1 else 0.0
    throughput = count / mean_s if mean_s > 0 else 0.0

    print(f"\n=== {name} ===")
    for idx, d in enumerate(durations, 1):
        print(f"round {idx}: {d:.6f}s")
    print(f"mean: {mean_s:.6f}s")
    print(f"std:  {std_s:.6f}s")
    print(f"throughput: {throughput:,.0f} items/s")
