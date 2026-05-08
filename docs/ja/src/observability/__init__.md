# Observability モジュール

> 📅 最終更新日: 2026/05/08

Observability モジュールは CelestialFlow の可観測性機能を提供し、実行状態の監視、パフォーマンス指標の収集、エラー追跡、リモート制御を含みます。

## モジュール概要

Observability モジュールはシステムの実行状態を収集・集約・報告し、リアルタイムの監視ビューとリモート制御機能を提供します。

## ファイル説明

### コアコンポーネント

1. **core_observer.py** (`BaseObserver`, `CallbackObserver`)
   - **役割**: エグゼキューターライフサイクルオブザーバー基底クラスとコールバック式オブザーバー
   - **主要機能**:
     - **BaseObserver**: ライフサイクルイベントインターフェースを定義（`on_start`、`on_task_success`、`on_task_fail`、`on_task_duplicate`、`on_tasks_added`、`on_finish`）、サブクラスが必要に応じてオーバーライド
     - **CallbackObserver**: キーワード引数でコールバック関数を受け取り、サブクラス化不要

2. **core_report.py** (`TaskReporter`)
   - **役割**: タスク状態レポーター、実行状態を収集しリモート Web サーバーに報告
   - **主要機能**:
     - **状態報告**: タスクグラフの構造、トポロジー、実行状態、エラー情報を定期的にプッシュ
     - **タスク注入**: Web UI からユーザーが注入したタスクを受け取り、実行中のタスクグラフに動的に挿入
     - **パラメータ調整**: サーバーから設定を取得し、報告間隔を動的に調整
     - **エラー同期**: 2種類のエラープッシュモード（メタデータモードとコンテンツモード）をサポート
   - **プロトコル**: HTTP
   - **データ形式**: JSON

3. **core_progress.py** (`TaskProgress`)
   - **役割**: `BaseObserver` を継承した tqdm ベースのタスク進捗可視化
   - **主要機能**:
     - `on_start` でプログレスバーを作成
     - `on_task_success/fail/duplicate` で進捗を更新
     - `on_tasks_added` でタスク総数を動的に増加
     - `on_finish` でプログレスバーを閉じる

## モジュール関連

### 内部関連
- `BaseObserver` はオブザーバーパターンの基底クラス、`TaskProgress` と `CallbackObserver` はそれに基づいて実装
- `TaskReporter` は独立したプラグ可能なレポートコンポーネント

### 外部関連
- **Stage モジュール**: `TaskExecutor` は `list[BaseObserver]` を保持、`add_observer()` / `remove_observer()` で管理
- **Graph モジュール**: タスクグラフの構造とトポロジー情報を収集
- **Runtime モジュール**: 実行状態、パフォーマンス指標、エラー情報を収集
- **Persistence モジュール**: 永続化されたログとエラーデータを取得
- **Web モジュール**: Web UI との双方向通信

## アーキテクチャ

### Observer パターン
- **マルチキャスト**: `TaskExecutor` は `list[BaseObserver]` を内部に保持し、ライフサイクルポイントでイベントをブロードキャスト
- **同期ディスパッチ**: `_notify(method_name, *args, **kwargs)` でイベントを同期呼び出し
- **空リスト = Null 等価**: observer リストが空の場合、オーバーヘッドなし

## 使用方法

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
