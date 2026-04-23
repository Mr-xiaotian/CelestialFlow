# TaskReporter

> 📅 最終更新日: 2026/04/22

`TaskReporter` は、タスクグラフの実行状態を収集してリモート Web サーバー（CelestialFlow Web UI）に報告するバックグラウンドコンポーネントです。また、サーバーから制御コマンド（タスク注入など）を取得する役割も担います。

## 機能

- **状態報告**: タスクグラフの構造、トポロジー、実行状態（カウンター）、エラー情報などを定期的にプッシュします。
- **タスク注入**: Web UI からユーザーが注入した新しいタスクを受信し、実行中のタスクグラフに動的に挿入します。
- **パラメータの動的調整**: サーバーから設定（報告間隔など）を取得することをサポートします。
- **エラーログ同期**: エラーログの増分プッシュをサポートします。

## 使用方法

通常、直接インスタンス化する必要はなく、`TaskGraph` を通じて有効化します：

```python
graph = TaskGraph(...)
# Reporter を有効化し、ローカルのポート 5005 に接続
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

## API インタラクション

Reporter は以下の Web API と連携します：

- `GET /api/pull_interval`: 報告間隔を取得します。
- `GET /api/pull_history_limit`: 履歴レコードの最大保持数を取得します。
- `GET /api/pull_task_injection`: 注入されたタスクを取得します。
- `POST /api/push_status`: ランタイム状態のスナップショットをプッシュします。
- `POST /api/push_structure`: グラフ構造情報をプッシュします。
- `POST /api/push_analysis`: 分析情報をプッシュします。
- `POST /api/push_summary`: グラフサマリーをプッシュします。
- `POST /api/push_history`: ノード履歴トレンドデータをプッシュします。
- `POST /api/push_errors_meta` / `push_errors_content`: エラー情報をプッシュします。

## NullTaskReporter

Reporter が有効化されていない場合、`TaskGraph` は `NullTaskReporter` をプレースホルダーとして使用します。`start()` と `stop()` メソッドはノーオペレーションで、ネットワークリクエストは一切行いません。

```python
class NullTaskReporter:
    interval = 0
    history_limit = 20

    def start(self) -> None: ...
    def stop(self) -> None: ...
```
