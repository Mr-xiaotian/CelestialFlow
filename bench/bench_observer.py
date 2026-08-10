"""
bench_observer — 对比三种观察者模式的开销

测试同一批任务在以下三种场景下的耗时：
1. 无观察者（基准）
2. print 日志（PrintObserver）
3. tqdm 进度条（TaskProgress）
"""

import time
from typing import Any

from tqdm import tqdm

from celestialflow import BaseObserver, TaskExecutor

# ── 工作函数 ──────────────────────────────────────────────────────────


def fibonacci(n: Any) -> int:
    """同步版斐波那契 — 迭代 O(n)"""
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    elif n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1 or n == 2:
        return 1
    prev, curr = 1, 1
    for _ in range(3, n + 1):
        prev, curr = curr, prev + curr
    return curr


def cpu_intensive(x: int) -> int:
    """纯 CPU 密集型任务，用于放大观察者开销"""
    total = 0
    for i in range(x * 10_000):
        total += i * i
    return total


# ── PrintObserver（无 tqdm，纯 print）───────────────────────────────


class PrintObserver(BaseObserver):
    """基于 print 的日志观察者"""

    def __init__(self) -> None:
        """初始化"""
        self.name = ""
        self.total = 0

    def on_start(self, name: str, total: int) -> None:
        """
        启动回调

        :param name: 执行器名称
        :param total: 任务总数
        """
        self.name = name
        self.total = total
        print(f"[observer] start executor={name}, total={total}")

    def on_task_success(self, count: int = 1) -> None:
        """
        成功回调

        :param count: 成功数量
        """
        print(f"[observer] success +{count}")

    def on_task_fail(self, count: int = 1) -> None:
        """
        失败回调

        :param count: 失败数量
        """
        print(f"[observer] fail +{count}")

    def on_task_duplicate(self, count: int = 1) -> None:
        """
        重复回调

        :param count: 重复数量
        """
        print(f"[observer] duplicate +{count}")

    def on_tasks_added(self, count: int) -> None:
        """
        添加任务回调

        :param count: 新增数量
        """
        self.total += count
        print(f"[observer] tasks added +{count}, total={self.total}")

    def on_finish(self) -> None:
        """结束回调"""
        print(
            f"[observer] finish executor={self.name}, "
            f"succeeded/ total={self.total}"
        )


# ── TaskProgress（基于 tqdm）─────────────────────────────────────────


class TqdmObserver(BaseObserver):
    """基于 tqdm 的进度条观察者"""

    _bar: tqdm[Any]

    def on_start(self, _name: str, total: int) -> None:
        """
        启动回调

        :param _name: 执行器名称
        :param total: 任务总数
        """
        self._bar = tqdm(total=total, desc=_name)

    def on_task_success(self, count: int = 1) -> None:
        """
        成功回调

        :param count: 成功数量
        """
        self._bar.update(count)

    def on_task_fail(self, count: int = 1) -> None:
        """
        失败回调

        :param count: 失败数量
        """
        self._bar.update(count)

    def on_task_duplicate(self, count: int = 1) -> None:
        """
        重复回调

        :param count: 重复数量
        """
        self._bar.update(count)

    def on_tasks_added(self, count: int) -> None:
        """
        添加任务回调

        :param count: 新增数量
        """
        if count:
            self._bar.total += count
            self._bar.refresh()

    def on_finish(self) -> None:
        """结束回调"""
        self._bar.close()


# ── 基准函数 ──────────────────────────────────────────────────────────


def run_benchmark(
    name: str,
    task_data: list[Any],
    func: Any,
    *,
    observer: BaseObserver | None = None,
) -> float:
    """
    运行一次 benchmark 并返回耗时

    :param name: 执行器名称
    :param task_data: 任务数据
    :param func: 工作函数
    :param observer: 观察者实例，None 表示无观察者
    :returns: 耗时（秒）
    """
    executor = TaskExecutor(
        name,
        func,
        execution_mode="serial",
        max_workers=1,
        max_retries=0,
    )
    if observer is not None:
        executor.add_observer(observer)

    start = time.perf_counter()
    executor.run(task_data)
    elapsed = time.perf_counter() - start
    return elapsed


def bench_observer_overhead() -> None:
    """对比三种场景下的耗时"""

    # 轻量任务：让观察者 I/O 开销相对明显
    light_tasks: list[Any] = list(range(20, 30))
    # 较重任务：让 CPU 计算占主导
    heavy_tasks: list[Any] = [50, 55, 60, 65, 70, 75, 80]

    scenarios = [
        ("light_fib", light_tasks, fibonacci),
        ("heavy_fib", heavy_tasks, fibonacci),
    ]

    print("=" * 60)
    print("Observer Overhead Benchmark")
    print("=" * 60)

    for label, tasks, work_func in scenarios:
        print(f"\n--- {label} ({len(tasks)} tasks) ---")

        # 1. 无观察者
        t_no = run_benchmark(f"NoObserver-{label}", tasks, work_func, observer=None)
        print(f"  no observer : {t_no:.4f}s")

        # 2. print 观察者
        print_obs = PrintObserver()
        t_print = run_benchmark(
            f"PrintObserver-{label}", tasks, work_func, observer=print_obs
        )
        print(f"  print       : {t_print:.4f}s  (+{t_print - t_no:.4f}s / "
              f"{((t_print / t_no) - 1) * 100:.1f}%)")

        # 3. tqdm 观察者
        tqdm_obs = TqdmObserver()
        t_tqdm = run_benchmark(
            f"TqdmObserver-{label}", tasks, work_func, observer=tqdm_obs
        )
        print(f"  tqdm        : {t_tqdm:.4f}s  (+{t_tqdm - t_no:.4f}s / "
              f"{((t_tqdm / t_no) - 1) * 100:.1f}%)")


def bench_observer_multirun() -> None:
    """多轮 benchmark 取均值，减少偶然误差"""

    tasks: list[Any] = list(range(20, 30))
    runs = 5

    results: dict[str, list[float]] = {
        "no_observer": [],
        "print": [],
        "tqdm": [],
    }

    for run in range(runs):
        # 每轮重新创建独立的 PrintObserver / TqdmObserver
        t_no = run_benchmark(
            f"MultiRun-no-{run}", tasks, fibonacci, observer=None
        )
        t_print = run_benchmark(
            f"MultiRun-print-{run}", tasks, fibonacci,
            observer=PrintObserver(),
        )
        t_tqdm = run_benchmark(
            f"MultiRun-tqdm-{run}", tasks, fibonacci,
            observer=TqdmObserver(),
        )

        results["no_observer"].append(t_no)
        results["print"].append(t_print)
        results["tqdm"].append(t_tqdm)

        print(f"  Run {run + 1}: no={t_no:.4f}s  print={t_print:.4f}s  "
              f"tqdm={t_tqdm:.4f}s")

    print(f"\n--- Summary (averaged over {runs} runs) ---")
    for key, times in results.items():
        avg = sum(times) / len(times)
        print(f"  {key:15s}: avg={avg:.4f}s  "
              f"min={min(times):.4f}s  max={max(times):.4f}s")


def main() -> None:
    """入口"""
    bench_observer_overhead()
    print("\n" + "=" * 60)
    print("Multi-run benchmark")
    print("=" * 60)
    bench_observer_multirun()


if __name__ == "__main__":
    main()
