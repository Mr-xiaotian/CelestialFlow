# Observability モジュール

> 📅 最終更新日: 2026/05/24

Observability モジュールは CelestialFlow のオブザーバビリティ機能を提供し、実行状態の監視、パフォーマンスメトリクスの収集、エラー追跡、リモート制御を含みます。タスク実行プロセスを透明、監視可能、制御可能にします。

## モジュール概要

Observability モジュールはシステムの実行状態の収集、集約、報告を担当し、リアルタイムの監視ビューとリモート制御機能を提供します。このモジュールにより、ユーザーはタスク実行状態、パフォーマンスメトリクス、エラー情報をリアルタイムで把握し、システムの動作を動的に調整できます。

## エクスポート項目

| エクスポートシンボル | ソースモジュール | 説明 |
|---------|---------|------|
| `BaseObserver` | `core_observer` | エグゼキューターライフサイクルオブザーバーの基底クラス。`on_start`、`on_task_success`、`on_task_fail`、`on_task_duplicate`、`on_tasks_added`、`on_finish` などのイベントインターフェースを定義 |
| `CallbackObserver` | `core_observer` | キーワード引数でコールバック関数を渡すオブザーバー実装。サブクラスの定義が不要 |
| `TaskReporter` | `core_report` | タスク状態レポーター。バックグラウンドスレッドで定期的に Web サーバーへ実行状態をプッシュし、制御命令を取得 |
| `NullTaskReporter` | `core_report` | 空実装のタスクレポーター。レポート機能無効時のプレースホルダーオブジェクト。`start()` / `stop()` はいずれも空操作 |
| `TaskProgress` | `core_progress` | `tqdm` ベースのタスク進捗可視化ツール。`BaseObserver` を継承し、ターミナルにプログレスバーを自動表示 |

## ファイル説明

### コアコンポーネント

1. **core_observer.py** (`BaseObserver`, `CallbackObserver`)
   - **役割**: エグゼキューターライフサイクルオブザーバーの基底クラスとコールバック式オブザーバー
   - **主要機能**:
     - `BaseObserver`: ライフサイクルイベントインターフェースを定義（`on_start`、`on_task_success`、`on_task_fail`、`on_task_duplicate`、`on_tasks_added`、`on_finish`）。サブクラスが必要に応じてオーバーライド
     - `CallbackObserver`: キーワード引数でコールバック関数を渡し、サブクラスの定義が不要

2. **core_report.py** (`TaskReporter`, `NullTaskReporter`)
   - **役割**: タスク状態レポーターとその空実装
   - **主要機能**:
     - **状態報告**: タスクグラフの構造、トポロジー、実行状態、エラー情報を定期的にプッシュ
     - **タスク注入**: Web UI からユーザーが注入した新しいタスクを受信し、実行中のタスクグラフに動的に挿入
     - **パラメータ調整**: サーバーから設定を取得し、報告間隔などのパラメータを動的に調整
     - **エラー同期**: 2つのエラープッシュモード（メタデータモードとコンテンツモード）をサポート
     - **NullTaskReporter**: レポート機能無効時のプレースホルダーオブジェクト。ネットワークリクエストを一切行わない
   - **通信プロトコル**: HTTP
   - **データ形式**: JSON

3. **core_progress.py** (`TaskProgress`)
   - **役割**: `tqdm` ベースのタスク進捗可視化。`BaseObserver` を継承
   - **主要機能**:
     - `on_start` でプログレスバーを作成
     - `on_task_success/fail/duplicate` で進捗を更新
     - `on_tasks_added` でタスク総数を動的に増加
     - `on_finish` でプログレスバーを閉じる

## モジュール関連

### 内部関連
- `BaseObserver` はオブザーバーパターンの基底クラス。`TaskProgress` と `CallbackObserver` はこれに基づいて実装
- `TaskReporter` は独立した報告コンポーネントで、プラガブルに設計
- `NullTaskReporter` はレポート無効時の安全なプレースホルダーを提供

### 外部関連
- **Stage モジュール**: `TaskExecutor` が `list[BaseObserver]` を保持し、`add_observer()` / `remove_observer()` でオブザーバーを管理
- **Graph モジュール**: タスクグラフの構造とトポロジー情報を収集
- **Runtime モジュール**: 実行状態、パフォーマンスメトリクス、エラー情報を収集
- **Persistence モジュール**: 永続化されたログとエラーデータを取得
- **Web モジュール**: Web UI との双方向通信により、状態表示とリモート制御をサポート

## アーキテクチャ特性

### Observer パターン
- **マルチキャスト**: `TaskExecutor` が内部で `list[BaseObserver]` を維持し、ライフサイクルポイントでイベントをブロードキャスト
- **同期ディスパッチ**: `_notify(method_name, *args, **kwargs)` を通じてすべてのオブザーバーにイベントを同期的にディスパッチ
- **空リストは Null と等価**: オブザーバーリストが空の場合、オーバーヘッドなし

### 双方向通信（TaskReporter）
- **アップリンクチャネル**: 状態データを Web サーバーに報告
- **ダウンリンクチャネル**: Web サーバーから実行インスタンスに制御命令を送信
- **リアルタイム性**: リアルタイムの状態更新と即時制御をサポート

### フォールトトレランス設計
- ネットワーク中断時のグレースフルデグラデーション。メインフローの実行に影響を与えません
- `NullTaskReporter` はレポート無効時のオーバーヘッドなしのプレースホルダー

## 使用パターン

### Observer の使用
```python
from celestialflow import TaskExecutor, TaskProgress, CallbackObserver

# TaskProgress でプログレスバーを表示
executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)

# CallbackObserver でカスタム動作
observer = CallbackObserver(
    on_task_success=lambda count=1: print(f"成功: {count}"),
    on_finish=lambda: print("完了"),
)
executor.add_observer(observer)
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

### カスタム Observer + TaskReporter の組み合わせ

以下の例は、カスタム統計オブザーバーを定義し、`TaskReporter` および `TaskGraph` と組み合わせて、観測可能な完全なワークフローを構築する方法を示します：

```python
import asyncio
from celestialflow import TaskGraph, TaskExecutor, TaskStage, BaseObserver
from celestialflow.observability import TaskReporter
from celestialflow.persistence import LogInlet

# 1. カスタムオブザーバー：タスク実行結果を統計
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
        raise ValueError(f"数値 {item} をスキップ")
    return item * 2


async def main():
    # タスクグラフを作成
    graph = TaskGraph(schedule_mode="eager")
    stage = TaskStage("Processor", process_item, execution_mode="thread", max_workers=4)
    graph.set_stages([stage])

    # カスタムオブザーバーを stage のエグゼキューターに登録
    stats_observer = StatsObserver()
    stage.add_observer(stats_observer)

    # オプション：TaskReporter を有効化して Web UI に報告
    log_inlet = LogInlet()
    reporter = TaskReporter(
        host="127.0.0.1",
        port=5000,
        task_graph=graph,
        log_inlet=log_inlet,
    )
    reporter.start()

    # タスクグラフを起動
    await graph.start_graph({stage.get_tag(): list(range(20))})

    # レポーターを停止
    reporter.stop()

    # 統計結果を確認
    print(f"最終統計 - 成功: {stats_observer.success_count}, 失敗: {stats_observer.fail_count}")


asyncio.run(main())
```

この例は3種類の観測可能コンポーネントの連携を示しています：
- **カスタム Observer**: `BaseObserver` を継承しイベントメソッドをオーバーライドして統計情報を収集
- **TaskGraph 統合**: `TaskStage` に内蔵されたオブザーバーリストを通じてカスタムオブザーバーを登録
- **TaskReporter**: 実行状態を Web サーバーにプッシュして外部監視を実現
