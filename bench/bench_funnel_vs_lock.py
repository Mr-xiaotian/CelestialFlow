# bench/bench_funnel_vs_lock.py
"""对比 funnel（队列 + 单消费者）与加锁（``ValueWrapper``）两种共享状态同步机制。

两种机制解决的是同一个问题：多个生产者线程安全地更新同一份共享状态。
本 bench 在相同负载下（生产者数量、总记录数、单条记录处理开销）对比：

- ``lock``：生产者持锁直接更新 ``ValueWrapper``，写操作同步可见。
- ``nolock``：``ValueWrapper`` 刻意不加锁的基线，用于量化锁本身的开销。
- ``sharded``：每个生产者独享一个无锁计数器，结束时汇总（仅适用于可聚合负载）。
- ``funnel``：生产者只负责入队，由单个 spout 线程串行消费并更新状态（异步可见）。

注意 ``nolock`` 只能当作“无同步的性能上界”，不能当作正确性演示：在启用 GIL 的解释器上，
``counter.value += 1`` 的竞争窗口（数个字节码）远小于线程切换粒度，实测几乎不会丢更新；
在 free-threaded 构建下才会真正丢更新。

对比维度：

- ``submit``：生产者侧耗时，即"提交完全部记录"所需的墙钟时间，反映发送端成本。
- ``drain``：生产者提交完成后，接收端处理完剩余记录的时间，反映异步 backlog 的代价。
- ``total``：端到端耗时与吞吐。
- ``peak_pending``：队列积压峰值（funnel 的内存代价，lock 恒为 0）。
- ``order_violations``：单生产者内记录顺序错乱次数（funnel 由单消费者天然保证为 0）。
  ``lock`` / ``nolock`` / ``sharded`` 不建模记录流，该维度为 ``n/a``：
  加锁只保证单次更新的原子性，无法提供跨生产者的 FIFO 次序。
- ``reader_ops``：``--readers`` 指定的读线程在写阶段完成的读次数，用于观察读对写的干扰。

用法::

    uv run python bench/bench_funnel_vs_lock.py
    uv run python bench/bench_funnel_vs_lock.py --producers 8 --items 800000 --readers 2
    uv run python bench/bench_funnel_vs_lock.py --work-iters 200 --scenarios lock,funnel

如何解读：

- 端到端吞吐由接收端决定：lock 在临界区内完成处理，funnel 由单个消费者完成处理，
  两者串行的工作量相同，因此 ``total`` 通常接近，别指望 funnel 把吞吐量拉高。
- 真正的差异在 ``submit`` 与 ``peak_pending``：funnel 用“发送端不等接收端”换来更低的
  发送端耗时与突发吸收能力，代价是积压与内存占用无约束增长，没有背压。
- ``--work-iters 0`` 时考察纯粹的交接开销：lock 只需一次加解锁，funnel 需一次线程间
  交接，该场景下 funnel 的端到端通常明显更慢（本机约 8x）。
- ``--work-iters`` 调大后，处理开销被从发送端临界区移出，``submit`` 差距被放大，
  但受 GIL 限制，纯 CPU 负载的 ``total`` 仍接近。
- 两者语义并不等价：funnel 由单消费者天然提供跨生产者 FIFO 次序，而加锁只保证单次
  更新的原子性，要拿到同样的“有序单写流”需要额外设计（如分片 + 归并）。
- ``--readers`` 会同时争用 lock 的 ``ValueWrapper`` 锁与 funnel 的 ``PendingCounter`` 锁，
  用于观察读压力对写路径的干扰。
"""

from __future__ import annotations

import argparse
import statistics
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from celestialflow.funnel import BaseInlet, BaseSpout
from celestialflow.runtime.util_types import NoOpContext, ValueWrapper

PENDING_SAMPLE_INTERVAL = 0.0005
"""采样队列积压的间隔（秒）。受平台定时器精度限制，peak_pending 是真实峰值下界。"""


def apply_work(seed: int, iters: int) -> int:
    """
    模拟单条记录的处理开销（纯 CPU 变换）。

    :param seed: 变换输入
    :param iters: 迭代次数，0 表示不做任何处理
    :return: 变换结果，仅用于避免空转被优化掉
    :rtype: int
    """
    acc = seed + 1
    for i in range(iters):
        acc = ((acc * 33) ^ (i + seed)) & 0x7FFF_FFFF
    return acc


def split_evenly(total: int, parts: int) -> list[int]:
    """
    把 ``total`` 尽量均匀地拆成 ``parts`` 份。

    :param total: 待拆分的总量
    :param parts: 份数
    :return: 每份的数量列表
    :rtype: list[int]
    """
    base, remainder = divmod(total, parts)
    return [base + (1 if i < remainder else 0) for i in range(parts)]


class CountingInlet(BaseInlet):
    """漏斗入口：把 ``(producer_id, seq)`` 记录送入绑定的 spout 队列。"""

    def emit(self, producer_id: int, seq: int) -> None:
        """
        发送一条记录。

        :param producer_id: 生产者编号
        :param seq: 该生产者内部的递增序号
        :return: ``None``
        """
        self._funnel((producer_id, seq))


class CountingSpout(BaseSpout):
    """漏斗出口：单线程串行消费记录，统计条数并校验单生产者内的顺序。"""

    def __init__(self, work_iters: int) -> None:
        """
        初始化接收端。

        :param work_iters: 单条记录的模拟处理开销
        """
        super().__init__()
        self.total = 0
        self.order_violations = 0
        self._work_iters = work_iters
        self._last_seq: dict[int, int] = {}

    def _handle_record(self, record: Any) -> None:
        """
        处理单条记录：计入总数并检查该生产者的序号是否连续。

        :param record: ``(producer_id, seq)`` 记录
        :return: ``None``
        """
        producer_id, seq = record
        if self._work_iters:
            apply_work(seq, self._work_iters)

        expected = self._last_seq.get(producer_id, -1) + 1
        if seq != expected:
            self.order_violations += 1
        self._last_seq[producer_id] = seq
        self.total += 1


@dataclass(slots=True)
class ScenarioResult:
    """单次场景运行的原始结果。"""

    scenario: str
    items: int
    producers: int
    readers: int
    work_iters: int
    submit_seconds: float
    total_seconds: float
    final_count: int
    expected_count: int
    peak_pending: int
    order_violations: int
    reader_ops: int
    # 该场景是否建模了带序号的记录流（决定 ``order_violations`` 是否有意义）。
    tracks_order: bool = False

    @property
    def drain_seconds(self) -> float:
        """生产者提交完成后，接收端处理剩余记录的时间。"""
        return max(self.total_seconds - self.submit_seconds, 0.0)

    @property
    def submit_throughput(self) -> float:
        """生产者侧吞吐（条/秒）。"""
        return (
            self.items / self.submit_seconds
            if self.submit_seconds > 0
            else float("inf")
        )

    @property
    def total_throughput(self) -> float:
        """端到端吞吐（条/秒）。"""
        return (
            self.items / self.total_seconds if self.total_seconds > 0 else float("inf")
        )

    @property
    def correct(self) -> bool:
        """最终计数是否与预期一致。"""
        return self.final_count == self.expected_count


def run_value_wrapper_scenario(
    *,
    items: int,
    producers: int,
    readers: int,
    work_iters: int,
    use_lock: bool,
) -> ScenarioResult:
    """
    运行共享计数器场景：生产者直接更新 ``ValueWrapper``。

    :param items: 总记录数
    :param producers: 生产者线程数
    :param readers: 读线程数，读线程在写阶段持续调用 ``get()``
    :param work_iters: 单条记录的模拟处理开销
    :param use_lock: 是否为 ``ValueWrapper`` 挂载共享锁
    :return: 本次运行结果
    :rtype: ScenarioResult
    """
    counter = ValueWrapper(
        value=0, lock=threading.Lock() if use_lock else NoOpContext()
    )
    chunks = split_evenly(items, producers)
    stop_readers = threading.Event()
    reader_ops = [0] * readers

    def produce(count: int) -> None:
        for i in range(count):
            if work_iters:
                apply_work(i, work_iters)
            counter.add(1)

    def read(index: int) -> None:
        ops = 0
        while not stop_readers.is_set():
            counter.get()
            ops += 1
        reader_ops[index] = ops

    producer_threads = [
        threading.Thread(target=produce, args=(count,)) for count in chunks
    ]
    reader_threads = [threading.Thread(target=read, args=(i,)) for i in range(readers)]

    start = time.perf_counter()
    for thread in reader_threads:
        thread.start()
    for thread in producer_threads:
        thread.start()
    for thread in producer_threads:
        thread.join()
    submit_seconds = time.perf_counter() - start

    stop_readers.set()
    for thread in reader_threads:
        thread.join()
    total_seconds = time.perf_counter() - start

    return ScenarioResult(
        scenario="lock" if use_lock else "nolock",
        items=items,
        producers=producers,
        readers=readers,
        work_iters=work_iters,
        submit_seconds=submit_seconds,
        total_seconds=total_seconds,
        final_count=counter.get(),
        expected_count=items,
        peak_pending=0,
        order_violations=0,
        reader_ops=sum(reader_ops),
        tracks_order=False,
    )


def run_sharded_scenario(
    *,
    items: int,
    producers: int,
    work_iters: int,
) -> ScenarioResult:
    """
    运行分片计数器场景：每个生产者独享一个无锁计数器，结束时汇总。

    该方案无任何跨线程争用，但只适用于可聚合负载，无法表达共享记录流的顺序。

    :param items: 总记录数
    :param producers: 生产者线程数
    :param work_iters: 单条记录的模拟处理开销
    :return: 本次运行结果
    :rtype: ScenarioResult
    """
    chunks = split_evenly(items, producers)
    counters = [ValueWrapper(value=0, lock=NoOpContext()) for _ in range(producers)]

    def produce(index: int, count: int) -> None:
        counter = counters[index]
        for i in range(count):
            if work_iters:
                apply_work(i, work_iters)
            counter.add(1)

    threads = [
        threading.Thread(target=produce, args=(index, count))
        for index, count in enumerate(chunks)
    ]

    start = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    total_seconds = time.perf_counter() - start

    return ScenarioResult(
        scenario="sharded",
        items=items,
        producers=producers,
        readers=0,
        work_iters=work_iters,
        submit_seconds=total_seconds,
        total_seconds=total_seconds,
        final_count=sum(counter.get() for counter in counters),
        expected_count=items,
        peak_pending=0,
        order_violations=0,
        reader_ops=0,
    )


def run_funnel_scenario(
    *,
    items: int,
    producers: int,
    readers: int,
    work_iters: int,
) -> ScenarioResult:
    """
    运行漏斗场景：生产者只入队，单个 spout 线程串行消费并更新状态。

    :param items: 总记录数
    :param producers: 生产者线程数
    :param readers: 读线程数，读线程在写阶段持续读取 ``get_pending_count()``
    :param work_iters: 单条记录的模拟处理开销
    :return: 本次运行结果
    :rtype: ScenarioResult
    """
    spout = CountingSpout(work_iters)
    inlet = CountingInlet().bind_spout(spout)
    chunks = split_evenly(items, producers)
    stop_readers = threading.Event()
    reader_ops = [0] * readers
    peak_pending = 0

    def produce(producer_id: int, count: int) -> None:
        for seq in range(count):
            inlet.emit(producer_id, seq)

    def read(index: int) -> None:
        ops = 0
        while not stop_readers.is_set():
            spout.get_pending_count()
            ops += 1
        reader_ops[index] = ops

    producer_threads = [
        threading.Thread(target=produce, args=(index, count))
        for index, count in enumerate(chunks)
    ]
    reader_threads = [threading.Thread(target=read, args=(i,)) for i in range(readers)]

    spout.start()
    start = time.perf_counter()
    for thread in reader_threads:
        thread.start()
    for thread in producer_threads:
        thread.start()

    # 生产者运行期间采样积压峰值。
    while any(thread.is_alive() for thread in producer_threads):
        peak_pending = max(peak_pending, spout.get_pending_count())
        time.sleep(PENDING_SAMPLE_INTERVAL)

    for thread in producer_threads:
        thread.join()
    submit_seconds = time.perf_counter() - start

    # 读线程会与接收端的计数递减争用同一把锁，先停掉再排空。
    stop_readers.set()
    for thread in reader_threads:
        thread.join()

    while True:
        pending = spout.get_pending_count()
        peak_pending = max(peak_pending, pending)
        if pending == 0:
            break
        time.sleep(PENDING_SAMPLE_INTERVAL)
    total_seconds = time.perf_counter() - start

    spout.stop()

    return ScenarioResult(
        scenario="funnel",
        items=items,
        producers=producers,
        readers=readers,
        work_iters=work_iters,
        submit_seconds=submit_seconds,
        total_seconds=total_seconds,
        final_count=spout.total,
        expected_count=items,
        peak_pending=peak_pending,
        order_violations=spout.order_violations,
        reader_ops=sum(reader_ops),
        tracks_order=True,
    )


def build_scenarios(args: argparse.Namespace) -> dict[str, Any]:
    """
    按命令行参数构造场景名到运行函数的映射。

    :param args: 命令行参数
    :return: 有序场景映射
    :rtype: dict[str, Any]
    """
    factories = {
        "lock": lambda: run_value_wrapper_scenario(
            items=args.items,
            producers=args.producers,
            readers=args.readers,
            work_iters=args.work_iters,
            use_lock=True,
        ),
        "nolock": lambda: run_value_wrapper_scenario(
            items=args.items,
            producers=args.producers,
            readers=args.readers,
            work_iters=args.work_iters,
            use_lock=False,
        ),
        "sharded": lambda: run_sharded_scenario(
            items=args.items,
            producers=args.producers,
            work_iters=args.work_iters,
        ),
        "funnel": lambda: run_funnel_scenario(
            items=args.items,
            producers=args.producers,
            readers=args.readers,
            work_iters=args.work_iters,
        ),
    }

    selected: list[str] = []
    for name in args.scenarios.split(","):
        name = name.strip()
        if not name:
            continue
        if name not in factories:
            raise SystemExit(
                f"unknown scenario: {name} (available: {', '.join(factories)})"
            )
        if name not in selected:
            selected.append(name)
    if not selected:
        raise SystemExit("no scenario selected")

    return {name: factories[name] for name in selected}


def pstd(values: list[float]) -> float:
    """
    计算总体标准差。

    :param values: 样本列表
    :return: 总体标准差，样本不足两个时返回 0
    :rtype: float
    """
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def order_text(tracks_order: bool, violations: int) -> str:
    """
    格式化顺序校验结果。

    :param tracks_order: 该场景是否建模了带序号的记录流
    :param violations: 顺序错乱次数
    :return: 展示文本，不建模记录流的场景为 ``n/a``
    :rtype: str
    """
    if not tracks_order:
        return "n/a"
    return f"{violations:,}"


def print_scenario_block(name: str, runs: list[ScenarioResult]) -> None:
    """
    打印单个场景的逐轮结果与统计量。

    :param name: 场景名
    :param runs: 该场景的多次运行结果
    :return: ``None``
    """
    submits = [run.submit_seconds for run in runs]
    totals = [run.total_seconds for run in runs]
    drains = [run.drain_seconds for run in runs]

    print(f"\n=== {name} ===")
    for index, run in enumerate(runs, 1):
        print(
            f"  run {index}: submit {run.submit_seconds:.4f}s | "
            f"drain {run.drain_seconds:.4f}s | total {run.total_seconds:.4f}s | "
            f"count {run.final_count:,}/{run.expected_count:,} | "
            f"peak_pending {run.peak_pending:,} | "
            f"order_violations {order_text(run.tracks_order, run.order_violations)} | "
            f"reader_ops {run.reader_ops:,}"
        )
    print(f"  submit: mean {statistics.mean(submits):.4f}s std {pstd(submits):.4f}s")
    print(f"  drain:  mean {statistics.mean(drains):.4f}s")
    print(f"  total:  mean {statistics.mean(totals):.4f}s std {pstd(totals):.4f}s")
    print(
        f"  throughput(total): {statistics.mean([run.total_throughput for run in runs]):,.0f} items/s"
    )
    correct = sum(1 for run in runs if run.correct)
    print(f"  correct: {correct}/{len(runs)}")
    violations = sum(run.order_violations for run in runs)
    print(f"  order_violations: {order_text(runs[0].tracks_order, violations)}")


def print_summary(results: dict[str, list[ScenarioResult]]) -> None:
    """
    打印跨场景汇总表。

    :param results: 场景名到运行结果的映射
    :return: ``None``
    """
    print("\n=== Summary ===")
    print(
        f"{'scenario':<10} {'submit(s)':>10} {'drain(s)':>10} {'total(s)':>10} "
        f"{'total(items/s)':>16} {'correct':>9} {'peak_pending':>13} {'order_viol':>11}"
    )
    print("-" * 98)
    for name, runs in results.items():
        correct = sum(1 for run in runs if run.correct)
        peak = max(run.peak_pending for run in runs)
        violations = sum(run.order_violations for run in runs)
        print(
            f"{name:<10} "
            f"{statistics.mean([run.submit_seconds for run in runs]):>10.4f} "
            f"{statistics.mean([run.drain_seconds for run in runs]):>10.4f} "
            f"{statistics.mean([run.total_seconds for run in runs]):>10.4f} "
            f"{statistics.mean([run.total_throughput for run in runs]):>16,.0f} "
            f"{f'{correct}/{len(runs)}':>9} "
            f"{peak:>13,} "
            f"{order_text(runs[0].tracks_order, violations):>11}"
        )


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。

    :return: 解析结果
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Benchmark funnel (queue + single consumer) against locking (ValueWrapper)."
    )
    parser.add_argument(
        "--items", type=int, default=400_000, help="Total records/updates per run"
    )
    parser.add_argument(
        "--producers", type=int, default=4, help="Producer thread count"
    )
    parser.add_argument("--readers", type=int, default=0, help="Reader thread count")
    parser.add_argument(
        "--work-iters",
        type=int,
        default=0,
        help="Simulated CPU work per record (0 disables)",
    )
    parser.add_argument("--repeats", type=int, default=3, help="Runs per scenario")
    parser.add_argument(
        "--scenarios",
        type=str,
        default="lock,nolock,sharded,funnel",
        help="Comma separated scenarios to run",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """
    校验命令行参数的取值范围。

    :param args: 命令行参数
    :raises SystemExit: 参数非法时退出
    """
    if args.items < 0:
        raise SystemExit("--items must be >= 0")
    if args.producers < 1:
        raise SystemExit("--producers must be >= 1")
    if args.readers < 0:
        raise SystemExit("--readers must be >= 0")
    if args.work_iters < 0:
        raise SystemExit("--work-iters must be >= 0")
    if args.repeats < 1:
        raise SystemExit("--repeats must be >= 1")


def main() -> None:
    """运行全部选定场景并输出对比结果。"""
    args = parse_args()
    validate_args(args)
    factories = build_scenarios(args)

    if args.producers < 2:
        print("warning: producers < 2 means there is no contention to observe")
    if args.producers > 1 and args.readers:
        print(
            "note: readers spin on the same lock as the writers, expect heavy interference"
        )

    gil_probe = getattr(sys, "_is_gil_enabled", None)
    gil_enabled = bool(gil_probe()) if callable(gil_probe) else None
    gil_text = (
        "unknown" if gil_enabled is None else ("enabled" if gil_enabled else "disabled")
    )

    print("=" * 98)
    print("Funnel vs Lock Benchmark")
    print("=" * 98)
    print(f"python       = {sys.version.splitlines()[0]}")
    print(f"GIL          = {gil_text}")
    print(f"items        = {args.items:,}")
    print(f"producers    = {args.producers}")
    print(f"readers      = {args.readers}")
    print(f"work_iters   = {args.work_iters}")
    print(f"repeats      = {args.repeats}")
    print(f"scenarios    = {', '.join(factories)}")

    results: dict[str, list[ScenarioResult]] = {name: [] for name in factories}
    for _ in range(args.repeats):
        for name, factory in factories.items():
            results[name].append(factory())

    for name, runs in results.items():
        print_scenario_block(name, runs)
    print_summary(results)


if __name__ == "__main__":
    main()
