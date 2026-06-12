# ランタイムキューテスト (test_queue.py)

> 📅 最終更新日: 2026/06/11

## 役割
タスクが異なるノード（Stage）間を流れる際のキュー管理ロジック（タスクのエンキュー/デキュー、終了信号のマージとブロードキャスト、キューの動的拡張を含む）を検証します。

## コアテスト対象
- `TaskInQueue`: Python 標準の `queue.Queue` をラップし、複数上流信号のマージを担当。
- `TaskOutQueue`: 複数の下流ノードへのブロードキャストまたは定向送信を担当。

## 主要テストシナリオ

### `TestTaskInQueue` — 入力キュー
| ケース | カバレッジ目標 |
|--------|--------------|
| `test_put_and_get_task` | 基本アクセス：`TaskEnvelope` のエンキューとデキュー |
| `test_input_termination_direct_exit` | 外部注入された `TerminationSignal` が直接返される |
| `test_multi_source_termination_merge` | 複数上流の終了信号がすべて到着した後にマージされて返される |
| `test_unknown_source_termination_raises` | 不明な送信元の終了信号が `UnknownNodeError` をスロー |
| `test_drain_returns_remaining_tasks` | `drain()` がキューをクリアし、残りの全タスクを返す |

### `TestTaskOutQueue` — 出力キュー
| ケース | カバレッジ目標 |
|--------|--------------|
| `test_put_broadcasts_to_all` | `put()` がすべての下流キューにブロードキャスト |
| `test_put_target_single_queue` | `put_target()` が指定キューにのみ送信 |
| `test_add_queue` | 出力キューの動的追加 |
| `test_duplicate_queue_name_raises` | 重複ターゲット名が `DuplicateNodeError` をスロー |

## テストの重点
- **信号同期**: 複数上流環境で、ある上流の早期終了によって他上流のデータが失われないことを確認。
- **型安全性**: キューから取得したオブジェクトが期待される `TaskEnvelope` または `TerminationIdPool` 型に適合することを検証。
- **ファンアウトロジック**: `TaskOutQueue` が一対多のデータ分配を効率的に処理できることを確認。

## 実行方法

```bash
# 全テスト実行
pytest tests/runtime/test_queue.py -v

# 入力キューテストのみ
pytest tests/runtime/test_queue.py -k "InQueue" -v

# 出力キューテストのみ
pytest tests/runtime/test_queue.py -k "OutQueue" -v

# 信号マージテストのみ
pytest tests/runtime/test_queue.py -k "termination" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestTaskInQueue` / `TestTaskOutQueue` | ~0.2s（キュー操作はすべてメモリ内で実行） |

## 重要な詳細
- `TerminationIdPool` を使用して全送信元の終了IDを集約し、後続のトレースを容易にします。
- `test_duplicate_queue_name_raises` はグラフ構造定義の厳密性を検証します。

## 注意事項
- キュー機構は CelestialFlow の非同期ノンブロッキングアーキテクチャの中核的な柱です。
- 関連実装は `src/celestialflow/runtime/core_queue.py` にあります。
