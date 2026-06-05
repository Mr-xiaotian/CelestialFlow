# Utils モジュール

> 📅 最終更新日: 2026/05/24

Utils モジュールは、CelestialFlow の汎用ユーティリティ関数とヘルパークラスを提供します。パフォーマンスベンチマーク、データクローン、コレクション操作、フォーマット機能が含まれます。これらのツールは他のモジュールで広く使用され、コードの再利用性と保守性を向上させます。

## ファイル一覧

| ファイル | 説明 |
|------|------|
| `util_benchmark.py` | エグゼキューターとタスクグラフのパフォーマンスベンチマーク |
| `util_clone.py` | エグゼキューターとタスクグラフのディープクローンツール |
| `util_collections.py` | コレクション操作ツール、`cluster_by_value_sorted()` を提供 |
| `util_format.py` | データフォーマットおよび表示ツール（`format_repr`, `format_table`, `format_duration`, `format_timestamp`, `format_avg_time`） |

> **注意**: `util_debug.py` はソースコードに存在しなくなりました。このファイルに依存しないでください。

## ファイル説明

### パフォーマンスツール

1. **util_benchmark.py**
   - **役割**: 異なる実行モード間のパフォーマンス差を比較するためのエグゼキューターとタスクグラフのパフォーマンスベンチマークツール
   - **主要関数**:
     - `benchmark_executor()`: `TaskExecutor` のベンチマークを実行し、serial/thread/async モードの実行時間を比較します
     - `benchmark_graph()`: `TaskGraph` のベンチマークを実行し、異なる stage_mode × execution_mode の組み合わせを比較します
   - **依存関係**: `util_clone`（エグゼキューター/タスクグラフのクローン）、`util_format`（時刻テーブル出力）
   - **使用シナリオ**:
     - タスク実行モード選択の最適化
     - パフォーマンスボトルネックの発見
     - 並列化効果の検証

### データ処理ツール

2. **util_clone.py**
   - **役割**: ベンチマークテストで状態を分離するためのエグゼキューターおよびタスクグラフのクローンツール
   - **主要関数**: `clone_executor()`, `clone_graph()`
   - **設計**: `copy.deepcopy` で独立したコピーを作成し、状態汚染を回避します
   - **サポート型**: `TaskExecutor`, `TaskGraph`
   - **使用シナリオ**: ベンチマーク、状態分離テスト

3. **util_collections.py**
   - **役割**: 特定のデータ処理機能を提供するコレクション操作ツール
   - **主要関数**: `cluster_by_value_sorted()`: 値に基づいて辞書をクラスタリングおよびソートします
   - **主要機能**:
     - 辞書を値でグループ化
     - グループ化結果のソート
     - 値でソートされたクラスタリング結果の返却
   - **使用シナリオ**: データ分析、結果グルーピング、統計サマリー、パフォーマンスメトリクスクラスタリング

4. **util_format.py**
   - **役割**: 可読性を向上させるデータフォーマットおよび表示ツール
   - **主要関数**:
     - `format_repr()`: 最大長制限付きでオブジェクトの文字列表現をフォーマットします
     - `format_table()`: 配置と枠線付きで表形式データをフォーマットします
     - `format_duration()`: 時間間隔をフォーマットします（秒を可読形式に変換）
     - `format_timestamp()`: タイムスタンプをフォーマットします
     - `format_avg_time()`: 平均処理時間をフォーマットします
   - **主要機能**: データ整形、テーブル生成、時刻フォーマット、パフォーマンスメトリクス表示
   - **使用シナリオ**: ログ出力、パフォーマンスレポート、ベンチマーク結果表示、デバッグ情報フォーマット

## モジュール関連

### 内部関連
- `util_benchmark` は `util_clone`（エグゼキューター/タスクグラフのクローン）および `util_format`（テーブル出力）に依存します
- その他のツールは相互に独立しており、単独で使用可能です

### 外部関連
- **Runtime モジュールとの関連**: パフォーマンステストツールでエグゼキューターの性能をテスト
- **Stage モジュールとの関連**: クローンツールでエグゼキューターコピーを生成
- **Graph モジュールとの関連**: クローンツールでタスクグラフコピーを生成、コレクションツールでグラフデータを操作
- **Persistence モジュールとの関連**: フォーマットツールでデータシリアライゼーションを表示

## 設計原則

### 単一責任
- 各ツールファイルは1カテゴリの問題のみを解決します
- 関数は小さく焦点を絞って設計され、機能肥大化を回避します
- 明確なインターフェースと明確な責任

### 純粋関数設計
- ユーティリティ関数は可能な限りステートレスです
- グローバル変数と副作用を回避します
- 並行安全な使用をサポートします

## 使用パターン

### ベンチマーク
```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.utils.util_benchmark import benchmark_executor

executor = TaskExecutor("Bench", my_func)
asyncio.run(benchmark_executor(executor, async_executor, range(100)))
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
# {"1": ["a", "c"], "2": ["b"]}
```

### フォーマット
```python
from celestialflow.utils.util_format import format_table, format_duration

print(format_table([[2.34, 0.89]], ["serial", "thread"], ["Time"]))
print(format_duration(123.456))  # "2m 3.46s"
```

## 使用例

### すべてのツール関数の一括インポートと使用

以下はすべてのツールモジュールを一度にインポートし、各関数を使用する例です：

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

# 1. フォーマットツール ----
print("=" * 40)
print("フォーマットツール例")
print("=" * 40)

# format_duration: 秒 -> 可読時間
print(f"format_duration(75): {format_duration(75)}")     # 01:15
print(f"format_duration(3661): {format_duration(3661)}") # 01:01:01

# format_timestamp: タイムスタンプ -> 日付文字列
import time
print(f"format_timestamp(now): {format_timestamp(time.time())}")

# format_avg_time: 平均処理時間
print(f"format_avg_time(12.5, 100): {format_avg_time(12.5, 100)}")  # 0.12s/it
print(f"format_avg_time(2.0, 1): {format_avg_time(2.0, 1)}")       # 2.00s/it

# format_repr: 安全に切り捨て
print(f"format_repr('hello'*10, 15): {format_repr('hello'*10, 15)}")

# 2. コレクション操作 ----
print("\n" + "=" * 40)
print("コレクション操作例")
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
    print(f"処理量 {value}: {stages}")
# 出力：
#   処理量 50: ['stage_b', 'stage_d']
#   処理量 100: ['stage_a', 'stage_c']
#   処理量 200: ['stage_e']

# 3. クローンツール（ベンチマークと組み合わせて）----
print("\n" + "=" * 40)
print("クローンとベンチマーク例")
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

    # エグゼキューターをクローンして分離された状態でテスト
    cloned = clone_executor(executor)
    print(f"元のエグゼキューター: {executor.get_name()}")
    print(f"クローンしたエグゼキューター: {cloned.get_name()}")
    print(f"モード一致: {executor.execution_mode == cloned.execution_mode}")

    # format_table でテーブルを表示
    table = format_table(
        [[100, 0.12], [50, 0.08]],
        row_names=["thread", "serial"],
        column_names=["タスク数", "平均処理時間(s)"],
    )
    print(f"\nベンチマークテーブル:\n{table}")

    # 元のエグゼキューターを実行
    await executor.start(range(100))


asyncio.run(run_benchmark())
```
