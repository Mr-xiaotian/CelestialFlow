# Observability モジュール

> 📅 最終更新日: 2026/05/08

Observability モジュールは CelestialFlow のオブザーバビリティ機能を提供し、実行状態の監視、パフォーマンスメトリクスの収集、エラー追跡、リモート制御を含みます。タスク実行プロセスを透明、監視可能、制御可能にします。

## モジュール概要

Observability モジュールはシステムの実行状態の収集、集約、報告を担当し、リアルタイムの監視ビューとリモート制御機能を提供します。このモジュールにより、ユーザーはタスク実行状態、パフォーマンスメトリクス、エラー情報をリアルタイムで監視し、システムの動作を動的に調整できます。

## ファイル説明

### コアコンポーネント

1. **core_observer.py** (`BaseObserver`, `CallbackObserver`)
   - **役割**: エグゼキューターライフサイクルオブザーバーの基底クラスとコールバック式オブザーバー
   - **主要機能**:
     - **BaseObserver**: ライフサイクルイベントインターフェースを定義（`on_start`、`on_task_success`、`on_task_fail`、`on_task_duplicate`、`on_tasks_added`、`on_finish`）。サブクラスが必要に応じてオーバーライド
     - **CallbackObserver**: キーワード引数でコールバック関数を渡し、サブクラスの定義が不要

2. **core_report.py** (`TaskReporter`)
   - **役割**: タスク状態レポーター。実行状態を収集しリモート Web サーバーに報告
   - **主要機能**:
     - **状態報告**: タスクグラフの構造、トポロジー、実行状態、エラー情報を定期的にプッシュ
     - **タスク注入**: Web UI からユーザーが注入した新しいタスクを受信し、実行中のタスクグラフに動的に挿入
     - **パラメータ調整**: サーバーから設定を取得し、報告間隔などのパラメータを動的に調整
     - **エラー同期**: 2つのエラープッシュモード（メタデータモードとコンテンツモード）をサポート
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
- **ダウンリンクチャネル**: Web サーバーから実行インスタンスに制御コマンドを送信
- **リアルタイム**: リアルタイムの状態更新と即時制御をサポート

### フォールトトレランス設計
- ネットワーク中断時のローカルキャッシュとリトライ
- メインの実行フローに影響を与えないグレースフルデグラデーション

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
