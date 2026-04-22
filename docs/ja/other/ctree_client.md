# CelestialTree クライアント

CelestialFlow は `celestialtree` クライアントを統合しており、きめ細かなタスクの全チェーン追跡（Provenance）とイベント記録を実現します。

## はじめに

CelestialTree は独立したイベントソーシングシステムです。CelestialFlow は `CelestialTreeClient` を使用して、タスクのライフサイクル中の重要なイベント（入力、成功、失敗、リトライ、分裂、ルーティングなど）を CelestialTree サービスに送信します。

これにより、ユーザーは以下のことが可能になります：
1. **データリネージの追跡**: ある結果がどの元のタスクから、どのステップを経て生成されたかをクエリできます。
2. **エラー根本原因の特定**: 失敗したタスクの上流ソースをクエリできます。
3. **実行ツリーの可視化**: タスク実行のコールツリーを生成できます。

## 設定

`TaskGraph` の初期化時に設定します：

```python
graph.set_ctree(
    use_ctree=True,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778
)
```

## イベントタイプ

フレームワークは以下のタイプのイベントを自動的に発行します：

- `task.input`: タスクが Stage に入ります。
- `task.success`: タスクが正常に処理されました。
- `task.error`: タスクの処理が失敗しました。
- `task.retry.N`: タスクの N 回目のリトライです。
- `task.split`: タスクが分裂しました。
- `task.route`: タスクがルーティングされました。
- `task.duplicate`: 重複タスクが検出されました。
- `termination.input` / `termination.merge`: 終了シグナルのフローです。

## 来歴クエリ

`TaskGraph` は来歴情報をクエリするための簡素化されたラッパーメソッドを提供します：

### get_stage_input_trace

指定した Stage の現在のすべての入力タスクの来歴ツリー（つまり、各タスクの出所）を取得します。

```python
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
print(trace_str)
```

### get_error_trace

特定のエラー ID の来歴ツリーを取得します。

```python
trace_str = graph.get_error_trace(error_id=12345)
print(trace_str)
```
