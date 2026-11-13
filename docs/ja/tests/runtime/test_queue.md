# tests/runtime/test_queue.py

> 📅 最終更新日: 2026/11/13

## 役割
タスクが異なるノード間を流れる際のキュー管理ロジック（タスクのエンキュー / デキュー、終了信号のマージとブロードキャスト、キューの動的拡張を含む）を検証します。

## コアテスト対象
- `TaskInQueue`: Python 標準の `queue.Queue` をラップし、複数の上流からの信号のマージを担当します。
- `TaskOutQueue`: 複数の下流ノードへのブロードキャストまたはターゲット指定送信を担当します。

## 主要テストシナリオ

### `TestTaskInQueue` — 入力キュー
`simple_queue` fixture は上流ソースを持たない入力キュー（`out_name="test"` のみ）を構築し、単一ソースのケースで再利用します。

| ケース | カバレッジ目標 |
|------|----------|
| `test_put_and_get_task` | 基本アクセス：`TaskEnvelope` をエンキュー / デキューし、タスクと ID がそのまま返る |
| `test_input_termination_direct_exit` | ソースが `"input"` の `TerminationSignal` が、その ID のみを含む `TerminationIdPool` へ直接変換される |
| `test_multi_source_termination_merge` | 2 つの上流がそれぞれ 1 回終了信号を送信した後、`get()` が `{10, 20}` を含むマージ済み ID プールを返す（アサート時はソートして比較；実装上、すべての上流が揃わないと `get()` は待ち続ける） |
| `test_unknown_source_termination_raises` | 不明なソースの終了信号が `UnknownNodeError` を送出する（`"unknown queue source name"` にマッチ） |
| `test_drain_returns_remaining_tasks` | `drain()` がキューを空にし、残りのすべてのタスクをエンキュー順で返し、キューは空になる |

### `TestTaskOutQueue` — 出力キュー
出力キューは標準ライブラリ `queue.Queue` を実際の受け皿として使用し、ブロードキャスト / ターゲット指定送信の可視的な結果を検証します。

| ケース | カバレッジ目標 |
|------|----------|
| `test_put_broadcasts_to_all` | `put()` が同じエンベロープをすべての下流キューへブロードキャストする |
| `test_put_target_single_queue` | `put_target()` が指定キューにのみ送信し、他のキューは空のまま |
| `test_add_queue` | 出力キューを動的に追加した後、新しいキューもブロードキャストを受信する |
| `test_duplicate_queue_name_raises` | 重複したターゲット名が `DuplicateNodeError` を送出する（`"duplicate queue target name"` にマッチ） |

## テストの重点
- **信号同期**: 複数上流環境で、ある上流の早期終了によって他上流のデータが失われないことを確認。
- **型安全性**: キューから取得したオブジェクトが期待される `TaskEnvelope` または `TerminationIdPool` 型に適合することを検証。
- **ファンアウトロジック**: `TaskOutQueue` が一対多のデータ分配を効率的に処理できることを確認。

## 実行方法

```bash
# すべて実行
uv run pytest tests/runtime/test_queue.py -v

# 入力キューテストのみ
uv run pytest tests/runtime/test_queue.py::TestTaskInQueue -v

# 出力キューテストのみ
uv run pytest tests/runtime/test_queue.py::TestTaskOutQueue -v

# 信号マージテストのみ
uv run pytest tests/runtime/test_queue.py -k "termination" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|------|------|
| `TestTaskInQueue` / `TestTaskOutQueue` | < 0.1s（キュー操作はすべてメモリ内で完了） |

## 重要な詳細
- `TerminationIdPool` を使用して全ソースの終了 ID を集約し、後続のトレースを容易にします。
- `TaskInQueue.drain()` は `TaskEnvelope` のみを返し、途中で遭遇した終了信号は `termination_dict` に記録するだけで、ID プールは返しません。
- 重複したソース名 / 重複したターゲット名はそれぞれ `add_source_name` と `add_queue` が `DuplicateNodeError` を送出します；本ファイルは後者のみをカバーします。
- `test_duplicate_queue_name_raises` はグラフ構造定義の厳密性を検証します。

## 注意事項
- キュー機構は CelestialFlow の非同期ノンブロッキングアーキテクチャの中核的な柱です。
- 関連実装は `src/celestialflow/runtime/core_queue.py` にあります。
