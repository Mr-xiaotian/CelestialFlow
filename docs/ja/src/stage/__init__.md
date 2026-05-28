# Stage モジュール

> 📅 最終更新日: 2026/05/28

Stage モジュールは、CelestialFlow のタスク実行ユニットを定義します。基本的なタスクエグゼキューターから複雑なタスクノードまでの完全な体系を提供し、タスクグラフを構築するための基本ビルディングブロックです。

## モジュール概要

Stage モジュールは3つのレベルのタスク実行ユニットを含みます：
1. **TaskExecutor**: 基本タスクエグゼキューター、単一タスクの実行ロジックを処理
2. **TaskStage**: 拡張タスクノード、グラフ接続機能を追加
3. **定義済みノード**: スプリッター、ルーターなどの一般的なタスクパターンの実装

これらのコンポーネントがタスク実行のコアを構成し、それぞれ独立して使用することも、複雑なタスクフローに組み合わせることもできます。

## ファイル説明

### コアファイル

1. **core_executor.py** (`TaskExecutor`)
   - **役割**: 単一タスクの実行、並行制御、エラーハンドリング、リトライメカニズムを処理する基本タスクエグゼキューター
   - **主要機能**:
     - 同期/非同期タスク実行
     - エラーハンドリングとリトライ戦略
     - タイムアウト制御
     - 進捗報告とログ記録
     - リソース管理とクリーンアップ

2. **core_stage.py** (`TaskStage`)
   - **役割**: `TaskExecutor` を継承し、グラフ構造接続機能を追加した拡張タスクノード
   - **主要機能**:
     - 入力/出力キュー接続
     - 自動依存関係管理
     - グラフ構造対応の実行
     - 並列および直列接続
     - 状態管理とライフサイクル制御

3. **core_stages.py** (定義済みノード: `TaskSplitter`, `TaskRouter`, `TaskRedisTransport`, `TaskRedisSource`, `TaskRedisAck`)
   - **役割**: 複雑なワークフロー構築を簡素化する一般的なタスクパターンと Redis 統合ノードのプリ実装
   - **含まれるノード**:
     - `TaskSplitter`: 入力を複数のサブタスクに分割
     - `TaskRouter`: 条件に基づいてタスクを異なる下流ノードにルーティング
     - `TaskRedisTransport`: クロス言語または分散実行のためにタスクを Redis キューに送信
     - `TaskRedisSource`: タスクグラフの入力ソースとして Redis キューからタスクを消費
     - `TaskRedisAck`: Redis Worker からの実行結果を受信し、タスク完了を確認

## モジュール関連

### 内部関連
- `TaskStage` は `TaskExecutor` を継承し、グラフ接続機能を拡張
- 定義済みノードは `TaskStage` の特殊化実装
- すべてのノードは `TaskGraph` 内で組み合わせて使用可能

### 外部関連
- **Graph モジュールとの関連**: `TaskStage` は `TaskGraph` の基本ビルディングユニット
- **Runtime モジュールとの関連**: ノード間通信に `TaskInQueue`/`TaskOutQueue` を使用、実行に `TaskDispatch` に依存
- **Utils モジュールとの関連**: データ処理と変換にユーティリティ関数を使用
- **Persistence モジュールとの関連**: タスク状態の永続化保存をサポート

## 使用パターン

### 基本的な使用
1. **エグゼキューター作成**: `TaskExecutor` を継承してカスタムビジネスロジックを実装
2. **ノードとしてラップ**: `TaskStage` でエグゼキューターをラップしてグラフ接続をサポート
3. **グラフ構造構築**: ノードを `TaskGraph` に追加し、依存関係を確立

### 高度な使用
1. **定義済みノードの使用**: `TaskSplitter`、`TaskRouter` などを直接使用して開発を簡素化
2. **ノードの組み合わせ**: 複数のノードを組み合わせて複雑なデータ処理パイプラインを構成
3. **カスタムノード**: `TaskStage` を継承してドメイン固有のノードタイプを作成

## 設計原則

### 単一責任
- 各 `TaskExecutor` は単一タイプのタスクのみを処理
- `TaskStage` はグラフ接続と状態管理に集中
- 定義済みノードは特定のデータ処理パターンを実装

### 組み合わせ可能性
- すべてのノードは統一インターフェースを使用し、自由に組み合わせ可能
- チェーン接続と並列処理をサポート
- 入力/出力型互換性チェック

### 拡張性
- 継承によるカスタムノードの容易な作成
- プラグインベースのアーキテクチャサポート
- 設定駆動、コード変更なしで動作を調整可能

## 使用例

以下に、stage モジュールの各コアクラスの典型的な使用例を示します。

### TaskExecutor のスタンドアロン使用

```python
from celestialflow import TaskExecutor

# 処理関数を定義
def process_item(x: int) -> dict:
    return {"input": x, "output": x * 10}

# 作成と実行
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

# 統計
print(f"成功: {executor.get_counts()['tasks_succeeded']}")
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
for name, stage in graph.stage_dict.items():
    summary = stage.get_summary()
    print(f"{name}: {summary}")

# グラフサマリー
print(graph.get_graph_summary())
```

### TaskSplitter の使用例

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
print(graph.get_graph_summary())
```

### TaskRouter の使用例

```python
from celestialflow import TaskGraph, TaskStage, TaskRouter

# ルーティング情報を生成する処理関数を定義
def classify(x: int) -> tuple:
    if x > 0:
        return ("positive", x)
    else:
        return ("negative", x)

source = TaskStage("Source", func=classify, stage_mode="serial")
router = TaskRouter("Router")
pos = TaskStage("Positive", func=lambda x: f"POS: {x}", stage_mode="serial")
neg = TaskStage("Negative", func=lambda x: f"NEG: {x}", stage_mode="serial")

graph = TaskGraph()
graph.set_stages([source, router, pos, neg])
graph.connect([source], [router])
graph.connect([router], [pos, neg])  # 2つの下流にルーティング

graph.start_graph({source.get_name(): [5, -3, 10, -8]})
print(graph.get_graph_summary())
```

## ベストプラクティス

1. **シンプルなタスク**: `TaskExecutor` を直接使用するか継承
2. **グラフノード**: 常に `TaskStage` またはサブクラスをグラフノードとして使用
3. **データ処理**: 重複コードを減らすために定義済みノードを優先使用
4. **エラーハンドリング**: `TaskExecutor` レベルで堅牢なエラーハンドリングを実装
5. **リソース管理**: `cleanup()` メソッドを適切に実装してリソースを解放
