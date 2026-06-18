# Stage モジュール

> 📅 最終更新日: 2026/06/17

Stage モジュールは CelestialFlow におけるタスク実行ユニットを定義します。基本的なタスク実行者から複雑なタスクノードまでの完全な体系を提供し、タスクグラフを構築するための基本構成要素です。

## エクスポートシンボル

| エクスポートシンボル | ソースモジュール | 説明 |
|---------|---------|------|
| `TaskExecutor` | `core_executor` | 基本タスク実行者。serial/thread/async の 3 つの実行モードをサポート |
| `TaskStage` | `core_stage` | 拡張タスクノード。TaskExecutor を継承し、グラフ接続機能と stage_mode 制御を追加 |
| `TaskSplitter` | `core_stages` | 定義済みノード：単一タスクを複数のサブタスクに分割 |
| `TaskRouter` | `core_stages` | 定義済みノード：条件に応じてタスクを異なる下流にルーティング |

> `AnyTaskStage` 型エイリアスは `util_types.py` で定義されており、`__all__` には含まれていません。

## モジュール概要

Stage モジュールは 3 つの階層のタスク実行ユニットで構成されます：
1. **TaskExecutor**: 基本タスク実行者。単一タスクの実行ロジックを処理
2. **TaskStage**: 拡張タスクノード。グラフ接続機能を追加
3. **定義済みノード**: 一般的なタスクパターンの実装。スプリッター、ルーターなど

これらのコンポーネントがタスク実行の中核を形成し、各コンポーネントは単独で、または組み合わせて複雑なタスクフローを構築できます。

## ファイル説明

### コアファイル

1. **core_executor.py** (`TaskExecutor`)
   - **役割**: 基本タスク実行者。単一タスクの実行、並行性制御、エラー処理、リトライ機構を担当
   - **主要機能**:
     - 同期/非同期タスク実行
     - エラー処理とリトライ戦略
     - Observer パターンによるライフサイクルブロードキャスト
     - 結果収集とエラー記録

2. **core_stage.py** (`TaskStage`)
   - **役割**: 拡張タスクノード。`TaskExecutor` を継承し、グラフ構造の接続機能を追加
   - **主要機能**:
     - `stage_mode`（serial/thread）による Graph 内でのスケジューリング方式の制御
     - Inlet バインディング（`set_inlet`）による fallback/log キューの永続化層への接続
     - 先行ノードカウンターバインディング（`prev_binding`）
     - 状態管理とライフサイクル制御（`NOT_STARTED → RUNNING → STOPPED`）

3. **core_stages.py** (定義済みノード: `TaskSplitter`, `TaskRouter`)
   - **役割**: 一般的な構造型タスクパターンの事前実装
   - **含まれるノード**:
     - `TaskSplitter`: 入力を複数のサブタスクに分配
     - `TaskRouter`: 条件に応じてタスクを異なる下流ノードにルーティング

4. **util_types.py** (`AnyTaskStage`)
   - **役割**: 任意のジェネリックパラメータを持つ Stage のための `TaskStage[Any, Any]` 型エイリアスを提供

## モジュール連携

### 内部連携
- `TaskStage` は `TaskExecutor` を継承し、グラフ接続機能を拡張
- 定義済みノードはすべて `TaskStage` の特殊化実装
- すべてのノードは `TaskGraph` 内で組み合わせて使用可能

### 外部連携
- **Graph モジュールとの連携**: `TaskStage` は `TaskGraph` の基本構成単位
- **Runtime モジュールとの連携**: ノード間通信に `TaskInQueue` / `TaskOutQueue` を使用し、`TaskDispatch` に依存して実行
- **Persistence モジュールとの連携**: `FallbackInlet` / `LogInlet` を通じてタスク状態を永続化
- **Observability モジュールとの連携**: `add_observer()` を通じて `BaseObserver` サブクラスを登録

## 使用例

以下は stage モジュールの各コアクラスの典型的な使用法です。

### TaskExecutor の単独使用

```python
from celestialflow import TaskExecutor

# 処理関数を定義
def process_item(x: int) -> int:
    return x * 10

# 作成して実行
executor = TaskExecutor(
    name="Calculator",
    func=process_item,
    execution_mode="serial",
)
executor.start([1, 2, 3])

# 結果を取得
success = executor.get_success_pairs()
for task, result in success:
    print(f"{task} -> {result}")
```

### TaskStage をグラフノードとして使用

```python
from celestialflow import TaskGraph, TaskStage

# ステージノードを作成
stage_a = TaskStage("StageA", func=lambda x: x + 1, stage_mode="thread")
stage_b = TaskStage("StageB", func=lambda x: x * 2, stage_mode="serial")

# グラフを構築
graph = TaskGraph()
graph.set_stages([stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# 実行
graph.start_graph({stage_a.get_name(): [5, 10, 15]})

# ステージスナップショット
for name, runtime in graph.stage_runtime_dict.items():
    summary = runtime.stage.get_summary()
    print(f"{name}: {summary}")
```

### TaskSplitter 使用例

```python
from celestialflow import TaskGraph, TaskStage, TaskSplitter

# カスタムスプリッター：文字列をカンマで分割
class CommaSplitter(TaskSplitter):
    def _split(self, *task):
        return tuple(task[0].split(","))

# グラフを構築
raw = TaskStage("Source", func=lambda x: x, stage_mode="serial")
splitter = CommaSplitter("Splitter")
processor = TaskStage("Process", func=lambda x: x.strip().upper(), stage_mode="thread")

graph = TaskGraph()
graph.set_stages([raw, splitter, processor])
graph.connect([raw], [splitter])
graph.connect([splitter], [processor])

graph.start_graph({raw.get_name(): ["a,b,c", "x,y,z"]})
```

### TaskRouter 使用例

```python
from celestialflow import TaskGraph, TaskStage, TaskRouter

# ルーティング関数を定義：タスク内容に基づいてターゲットノード名を返す
def classify(x: int) -> str:
    if x > 0:
        return "positive"
    else:
        return "negative"

# 上流は元のタスクのみを生成
source = TaskStage("Source", func=lambda x: x, stage_mode="serial")

# Router が内部でタスクをどの下流に送るか決定
router = TaskRouter("Router", classify)
pos = TaskStage("Positive", func=lambda x: f"POS: {x}", stage_mode="serial")
neg = TaskStage("Negative", func=lambda x: f"NEG: {x}", stage_mode="serial")

graph = TaskGraph()
graph.set_stages([source, router, pos, neg])
graph.connect([source], [router])
graph.connect([router], [pos, neg])

graph.start_graph({source.get_name(): [5, -3, 10, -8]})
```

## 設計原則

- **使い捨てオブジェクト**: `TaskExecutor` および `TaskStage` は使い捨て設計。一度の実行完了後は再利用すべきではない
- **単一責務**: 各 `TaskExecutor` は単一タイプのタスクのみを処理
- **組み合わせ可能性**: すべてのノードは統一インターフェースを使用し、`TaskGraph` 内で自由に組み合わせ可能
