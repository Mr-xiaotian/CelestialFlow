# Utils モジュール

> 📅 最終更新日: 2026/06/22

Utils モジュールは CelestialFlow の汎用ユーティリティ関数と補助クラスを提供します。パフォーマンスベンチマークテスト、データクローン、コレクション操作、フォーマット機能を含みます。これらのツールは他のモジュールで広く使用され、コードの再利用性と保守性を向上させます。

## ファイル一覧

| ファイル | 説明 |
|------|------|
| `util_benchmark.py` | 実行器とタスクグラフのパフォーマンスベンチマークテスト |
| `util_clone.py` | 実行器とタスクグラフのディープクローンツール |
| `util_collections.py` | コレクション操作ツール。`cluster_by_value_sorted()` を提供 |
| `util_format.py` | データフォーマットと表示ツール（`format_repr`, `format_table`, `format_duration`, `format_timestamp`, `format_avg_time`） |

> **注意**: `util_debug.py` はソースコードに存在しません。このファイルに依存しないでください。

## ファイル説明

### パフォーマンスツール

1. **util_benchmark.py**
   - **役割**: 実行器とタスクグラフのパフォーマンスベンチマークテストツール。異なる実行モードのパフォーマンス差異を比較
   - **主要関数**:
     - `benchmark_executor()`: 同期/非同期 `TaskExecutor` のベンチマークテスト。serial/thread/async モードの実行時間を比較
     - `benchmark_graph()`: `TaskGraph` のベンチマークテスト。異なる stage_mode × execution_mode の組み合わせを比較
   - **依存**: `util_clone`（実行器/タスクグラフのクローン）、`util_format`（時間テーブルの出力）
   - **使用シーン**: タスク実行モード選択の最適化、パフォーマンスボトルネックの発見、並列化効果の検証

### データ処理ツール

2. **util_clone.py**
   - **役割**: 実行器、ノード、タスクグラフのクローンツール。ベンチマークテストでの状態分離に使用
   - **主要関数**: `clone_executor()`, `clone_stage()`, `clone_graph()`
   - **設計**: 新しいインスタンスを構築し主要パラメータをコピーすることで独立したコピーを作成。状態汚染を防止
   - **サポート型**: `TaskExecutor`, `TaskStage`, `TaskGraph`
   - **使用シーン**: ベンチマークテスト、状態分離テスト

3. **util_collections.py**
   - **役割**: コレクション操作ツール。特定のデータ処理機能を提供
   - **主要関数**: `cluster_by_value_sorted()`: 値に基づいて辞書をクラスタリングおよびソート
   - **主要機能**:
     - 辞書を値でグループ化
     - グループ化結果をソート
     - 値でソートされたクラスタリング結果を返す
   - **使用シーン**: データ分析、結果のグループ化、統計サマリー、パフォーマンス指標のクラスタリング

4. **util_format.py**
   - **役割**: データフォーマットと表示ツール。可読性を向上
   - **主要関数**:
     - `format_repr()`: オブジェクトの文字列表現をフォーマット。最大長を制限
     - `format_table()`: テーブルデータをフォーマット。アライメントとボーダーをサポート
     - `format_duration()`: 時間間隔をフォーマット（秒を可読形式に変換）
     - `format_timestamp()`: タイムスタンプをフォーマット
     - `format_avg_time()`: 平均処理時間をフォーマット
   - **主要機能**: データ整形、テーブル生成、時間フォーマット、パフォーマンス指標表示
   - **使用シーン**: ログ出力、パフォーマンスレポート、ベンチマークテスト結果表示、デバッグ情報のフォーマット

## モジュール関連

### 内部関連
- `util_benchmark` は `util_clone`（実行器/タスクグラフのクローン）と `util_format`（テーブル出力）に依存
- その他のツールは相互に独立しており、単独で使用可能

### 外部関連
- **Runtime モジュールとの関連**: パフォーマンステストツールが実行器のパフォーマンステストに使用される
- **Stage モジュールとの関連**: クローンツールが実行器のコピー生成に使用される
- **Graph モジュールとの関連**: クローンツールがタスクグラフのコピー生成に、コレクションツールがグラフデータ操作に使用される
- **Persistence モジュールとの関連**: フォーマットツールがデータシリアライズ表示に使用される

## 設計原則

### 単一責任
- 各ツールファイルは1種類の問題のみを解決
- 関数設計は小さく特化し、機能膨張を回避
- 明確なインターフェースと明確な責任

### 純粋関数設計
- ツール関数は可能な限りステートレス
- グローバル変数と副作用を回避
- 並行安全な使用をサポート

## 使用パターン

### ベンチマークテスト
```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.utils.util_benchmark import benchmark_executor


def sync_task(x: int) -> int:
    return x * 2


async def async_task(x: int) -> int:
    await asyncio.sleep(0.001)
    return x * 2


sync_executor = TaskExecutor("SyncBench", sync_task)
async_executor = TaskExecutor("AsyncBench", async_task)
asyncio.run(benchmark_executor(sync_executor, async_executor, range(100)))
```

### クローン
```python
from celestialflow.utils.util_clone import clone_executor, clone_graph

executor_copy = clone_executor(original_executor)
graph_copy = clone_graph(original_graph)
```

### コレクション操作
```python
from celestialflow.utils.util_collections import cluster_by_value_sorted

grouped = cluster_by_value_sorted({"a": 1, "b": 2, "c": 1})
# {1: ["a", "c"], 2: ["b"]}
```

### フォーマット
```python
from celestialflow.utils.util_format import format_table, format_duration

print(format_table([[2.34, 0.89]], ["serial", "thread"], ["Time"]))
print(format_duration(123))  # "02:03"
```

## 使用例

### 一括インポートして全ツール関数を使用

以下の例は全ツールモジュールを一度にインポートし、各関数を使用する方法を示します：

```python
import asyncio
from celestialflow import TaskExecutor, format_table
from celestialflow.utils.util_benchmark import benchmark_executor
from celestialflow.utils.util_clone import clone_executor, clone_stage, clone_graph
from celestialflow.utils.util_collections import cluster_by_value_sorted
from celestialflow.utils.util_format import (
    format_repr,
    format_duration,
    format_timestamp,
    format_avg_time,
)

# 1. 格式化工具 ----
print("=" * 40)
print("格式化工具示例")
print("=" * 40)

# format_duration: 秒 -> 可读时间
print(f"format_duration(75): {format_duration(75)}")     # 01:15
print(f"format_duration(3661): {format_duration(3661)}") # 01:01:01

# format_timestamp: 时间戳 -> 日期字符串
import time
print(f"format_timestamp(now): {format_timestamp(time.time())}")

# format_avg_time: 平均耗时
print(f"format_avg_time(12.5, 100): {format_avg_time(12.5, 100)}")  # 0.12s/it
print(f"format_avg_time(2.0, 1): {format_avg_time(2.0, 1)}")       # 2.00s/it

# format_repr: 安全截断
print(f"format_repr('hello'*10, 15): {format_repr('hello'*10, 15)}")

# 2. 集合操作 ----
print("\n" + "=" * 40)
print("集合操作示例")
print("=" * 40)

task_results = {
    "stage_a": 100,
    "stage_b": 50,
    "stage_c": 100,
    "stage_d": 50,
    "stage_e": 200,
}
clustered = cluster_by_value_sorted(task_results)
for value, stages in clustered.items():
    print(f"处理量 {value}: {stages}")
# 输出：
#   处理量 50: ['stage_b', 'stage_d']
#   处理量 100: ['stage_a', 'stage_c']
#   处理量 200: ['stage_e']

# 3. 克隆工具（配合基准测试）----
print("\n" + "=" * 40)
print("克隆与基准测试示例")
print("=" * 40)


def simple_task(x: int) -> int:
    return x * x


async def run_benchmark():
    executor = TaskExecutor(
        "Bench",
        simple_task,
        execution_mode="thread",
        max_workers=4,
    )

    # 克隆执行器用于隔离的状态测试
    cloned = clone_executor(executor)
    print(f"原始执行器: {executor.get_name()}")
    print(f"克隆执行器: {cloned.get_name()}")
    print(f"模式一致: {executor.execution_mode == cloned.execution_mode}")

    # 使用 format_table 展示表格
    table = format_table(
        [[100, 0.12], [50, 0.08]],
        row_names=["thread", "serial"],
        column_names=["任务数", "平均耗时(s)"],
    )
    print(f"\n基准测试表格:\n{table}")

    # 运行原始执行器
    executor.start(range(100))


asyncio.run(run_benchmark())
```
