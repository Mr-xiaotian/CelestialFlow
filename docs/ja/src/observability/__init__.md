# Observability モジュール

> 📅 最終更新日: 2026/06/18

Observability モジュールは CelestialFlow の可観測性機能を提供し、実行状態の監視、進捗の可視化、Observer パターン、リモート状態レポートを含みます。タスク実行プロセスを透過的かつ監視可能にします。

## エクスポートシンボル

| エクスポートシンボル | ソースモジュール | 説明 |
|---------|---------|------|
| `BaseObserver` | `core_observer` | 実行者ライフサイクルオブザーバーの基底クラス。`on_start`、`on_task_success`、`on_task_fail`、`on_task_duplicate`、`on_tasks_added`、`on_finish` などのイベントインターフェースを定義 |
| `TaskProgress` | `core_progress` | `tqdm` ベースのタスク進捗可視化ツール。`BaseObserver` を継承 |
| `TaskReporter` | `core_report` | タスク状態レポーター。バックグラウンドスレッドで定期的に Web サーバーへ実行状態をプッシュし、制御指示をプル |
| `NullTaskReporter` | `core_report` | タスクレポーターの空実装。レポート機能を無効にする際のプレースホルダー |

> ⚠️ **非推奨**：以前のドキュメントでは `CallbackObserver` が記載されていましたが、このクラスのソースコード実装は `core_observer.py` から削除され、利用できなくなりました。

## ファイル説明

### コアコンポーネント

1. **core_observer.py** (`BaseObserver`)
   - **役割**: 実行者ライフサイクルオブザーバーの基底クラス
   - **主要機能**:
     - `BaseObserver`: ライフサイクルイベントインターフェースを定義。サブクラスが必要に応じてオーバーライド

2. **core_progress.py** (`TaskProgress`)
   - **役割**: `tqdm` ベースのタスク進捗可視化。`BaseObserver` を継承
   - **主要機能**:
     - `on_start` でプログレスバーを作成
     - `on_task_success/fail/duplicate` で進捗を更新
     - `on_tasks_added` で総タスク数を動的に増加
     - `on_finish` でプログレスバーを閉じる

3. **core_report.py** (`TaskReporter`, `NullTaskReporter`)
   - **役割**: タスク状態レポーターとその空実装
   - **主要機能**:
     - **状態レポート**: タスクグラフの構造、トポロジー、実行状態、エラー情報を定期的にプッシュ
     - **タスク注入**: Web UI からユーザーが注入した新規タスクを受信し、実行中のタスクグラフに動的挿入
     - **パラメータ調整**: サーバーから設定をプルし、レポート間隔などのパラメータを動的調整
     - **エラー同期**: 2 種類のエラープッシュモード（メタデータモードとコンテンツモード）をサポート
   - **通信プロトコル**: HTTP
   - **データ形式**: JSON

## モジュール連携

### 内部連携
- `BaseObserver` はオブザーバーパターンの基底クラスであり、`TaskProgress` はこれに基づいて実装
- `TaskReporter` は独立したレポートコンポーネントで、プラグ可能な設計
- `NullTaskReporter` はレポート無効時の安全なプレースホルダーを提供

### 外部連携
- **Stage モジュールとの連携**: `TaskExecutor` は `list[BaseObserver]` を保持し、`add_observer()` / `remove_observer()` でオブザーバーを管理
- **Graph モジュールとの連携**: `TaskReporter` はタスクグラフの構造とトポロジー情報を収集
- **Persistence モジュールとの連携**: 永続化されたログとエラーデータを取得し、`LogInlet` に依存

## アーキテクチャ特性

### Observer パターン
- **マルチキャスト**: `TaskExecutor` 内部で `list[BaseObserver]` を保持し、ライフサイクルの節目でイベントをブロードキャスト
- **同期配信**: イベントは `_notify(method_name, *args, **kwargs)` で全オブザーバーに同期的に呼び出し
- **空リストは Null 相当**: observer リストが空の場合、オーバーヘッドなし

### 双方向通信（TaskReporter）
- **アップリンク**: 状態データを Web サーバーにレポート
- **ダウンリンク**: 制御指示を Web サーバーから実行インスタンスに配信

### フォールトトレラント設計
- ネットワーク断時のグレースフルデグラデーション。メインフロー実行に影響しない
- `NullTaskReporter` はレポート無効時のオーバーヘッドゼロのプレースホルダー

## 使用パターン

### Observer の使用
```python
from celestialflow import TaskExecutor, TaskProgress

# TaskProgress でプログレスバーを表示
executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)
```

### TaskReporter の使用
```python
from celestialflow.observability import TaskReporter

reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=my_task_graph,
    log_inlet=log_inlet,
)
reporter.start()
```

## 使用例

### カスタム Observer + TaskReporter の併用

```python
from celestialflow import TaskGraph, TaskStage, BaseObserver
from celestialflow.observability import TaskReporter
from celestialflow.persistence import LogInlet

# 1. カスタムオブザーバー：タスク実行結果を集計
class StatsObserver(BaseObserver):
    def __init__(self):
        self.success_count = 0
        self.fail_count = 0

    def on_task_success(self, count: int = 1):
        self.success_count += count

    def on_task_fail(self, count: int = 1):
        self.fail_count += count

    def on_finish(self):
        print(f"実行終了：成功 {self.success_count}、失敗 {self.fail_count}")

# 2. タスク処理関数を定義
def process_item(item: int) -> int:
    if item % 5 == 0:
        raise ValueError(f"数字 {item} をスキップ")
    return item * 2

# タスクグラフを作成
graph = TaskGraph(schedule_mode="eager")
stage = TaskStage("Processor", process_item, execution_mode="thread", max_workers=4)
graph.set_stages([stage])

# カスタムオブザーバーを stage の実行者に登録
stats_observer = StatsObserver()
stage.add_observer(stats_observer)

# オプション：TaskReporter を有効化して Web UI にレポート
log_inlet = stage.log_inlet
reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=graph,
    log_inlet=log_inlet,
)
reporter.start()

# タスクグラフを起動
graph.start_graph({stage.get_name(): list(range(20))})

# レポーターを停止
reporter.stop()

# 統計結果を確認
print(f"最終統計 - 成功: {stats_observer.success_count}, 失敗: {stats_observer.fail_count}")
```

この例は 3 種類の可観測コンポーネントの連携を示しています：
- **カスタム Observer**: `BaseObserver` を継承しイベントメソッドをオーバーライドして統計情報を収集
- **TaskGraph 統合**: `TaskStage` 組み込みのオブザーバーリストを通じてカスタムオブザーバーを登録
- **TaskReporter**: 実行状態を Web サーバーにプッシュして外部監視に利用
