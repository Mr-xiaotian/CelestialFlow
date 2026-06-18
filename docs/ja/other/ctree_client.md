# CelestialTree Client

> 📅 最終更新日: 2026/06/18

CelestialFlow は `celestialtree` クライアントの接続をサポートし、細粒度のタスク全リンクトレース（Provenance）とイベント記録を実現します。

> `celestialtree` は現在 CelestialFlow のデフォルトランタイム依存から外されています。
> 本ページで紹介するトレース機能が必要な場合は、`celestialtree` を別途インストールするか、ソースリポジトリで `uv sync --group dev` を実行してください。

## 概要

CelestialTree は独立したイベントソーシングシステムです。CelestialFlow は `CelestialTreeClient` を通じて、タスクライフサイクル中の重要なイベント（入力、成功、失敗、リトライ、分割、ルーティングなど）を CelestialTree サービスに送信します。

これにより、ユーザーは以下を実行できます：
1. **データリネージの追跡**: ある結果がどの元タスクから、どのステップを経て生成されたかを照会する。
2. **エラー根本原因の特定**: あるエラータスクの上流ソースを照会する。
3. **実行ツリーの可視化**: タスク実行のコールツリーを生成する。

## インストール

```bash
# celestialflow がインストール済みで、CelestialTree のみ追加する場合
uv pip install celestialtree

# ソースリポジトリで開発/デモを実行する場合
uv sync --group dev
```

## 設定

現在の `TaskGraph.set_ctree()` はイベントクライアントインスタンスを受け取ります。旧版の `use_ctree=True` / `host=...` 形式ではありません。

`TaskGraph` 初期化後に設定します：

```python
from celestialtree import Client as CelestialTreeClient

ctree_client = CelestialTreeClient(
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778,
    transport="grpc",
)

graph.set_ctree(ctree_client)
```

## イベントタイプ

フレームワークは以下のタイプのイベントを自動的に発行します：

- `task.input`: タスクが Stage に入る。
- `task.success`: タスク処理が成功。
- `task.error`: タスク処理が失敗。
- `task.retry.N`: タスクの N 回目のリトライ。
- `task.split`: タスクの分割。
- `task.route`: タスクのルーティング。
- `task.duplicate`: 重複タスクの検出。
- `termination.input` / `termination.merge`: 終了信号のフロー。

## トレーサビリティ照会

`TaskGraph` はトレーサビリティ情報を照会するための簡略化されたラッパーメソッドを提供します：

### get_stage_input_trace

ある Stage の現在のすべての入力タスクのトレースツリー（すなわち、これらのタスクがそれぞれどこから来たか）を取得します。

```python
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
print(trace_str)
```

### get_error_trace

特定のエラー ID のトレースツリーを取得します。

```python
trace_str = graph.get_error_trace(error_id=12345)
print(trace_str)
```
