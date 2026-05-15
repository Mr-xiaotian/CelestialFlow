# TaskReporter

> 📅 最終更新日: 2026/05/15

`TaskReporter` はタスクグラフの実行状態を収集し、リモート Web サーバー（CelestialFlow Web UI）に報告するバックグラウンドコンポーネントです。また、サーバーからの制御コマンド（タスク注入など）の取得も担当します。

## 機能特性

- **状態報告**: タスクグラフの構造、トポロジー、実行状態（カウンター）、エラー情報などを定期的にプッシュ。
- **タスク注入**: Web UI からユーザーが注入した新しいタスクを受信し、実行中のタスクグラフに動的に挿入。
- **パラメータの動的調整**: サーバーからの設定取得（報告間隔など）をサポート。
- **エラーログ同期**: 増分エラーログプッシュをサポート。

## 使用方法

通常、直接インスタンス化する必要はなく、`TaskGraph` を通じて有効化します：

```python
graph = TaskGraph(...)
# Reporter を有効化し、ローカルポート 5005 に接続
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

## API 連携

Reporter は以下の Web API と連携します：

- `GET /api/pull_interval`: 報告間隔を取得。
- `GET /api/pull_history_limit`: 履歴レコードの最大保持数を取得。
- `GET /api/pull_task_injection`: 注入されたタスクを取得。
- `POST /api/push_status`: ランタイム状態スナップショットをプッシュ。
- `POST /api/push_structure`: グラフ構造情報をプッシュ。
- `POST /api/push_analysis`: 分析情報をプッシュ。
- `POST /api/push_summary`: グラフ概要をプッシュ。
- `POST /api/push_history`: ノード履歴トレンドデータをプッシュ。
- `POST /api/push_errors_meta` / `push_errors_content`: エラー情報をプッシュ。

## NullTaskReporter

Reporter が有効化されていない場合、`TaskGraph` はプレースホルダーとして `NullTaskReporter` を使用します。`start()` と `stop()` はノーオペレーションで、ネットワークリクエストは行われません。

```python
class NullTaskReporter:
    interval = 1
    history_limit = 20

    def start(self) -> None: ...
    def stop(self) -> None: ...
```
