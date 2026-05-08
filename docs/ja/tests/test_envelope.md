# test_envelope.py テスト説明

> 📅 最終更新日: 2026/05/08

## テスト目標

`TaskEnvelope` タスクエンベロープのコア動作を検証：構築、getter メソッド、遅延ハッシュ、属性の永続化、ハッシュの一貫性、メモリ最適化機構。

## テスト範囲

| テストクラス | テスト数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskEnvelope` | 7 | 構築と getter、source、change_id、異なるハッシュ、同一ハッシュ、遅延ハッシュ、slots |

### テスト詳細

#### `test_create_and_getters`
- **目標**: コンストラクタと getter メソッドが正しくエンベロープデータを作成・読み取ることを検証。

#### `test_lazy_hash`
- **目標**: `hash` が構築時に `None` で、`get_hash()` の初回呼び出し時にのみ計算されることを検証。

#### `test_slots_memory_efficient`
- **目標**: `__slots__` が有効で、動的属性の追加を阻止することを検証。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow.runtime.core_envelope.TaskEnvelope` | テスト対象 |

## 実行方法

```bash
pytest tests/test_envelope.py -v
```

## 関連ファイル

- `src/celestialflow/runtime/core_envelope.py`: テスト対象実装
- `src/celestialflow/runtime/util_hash.py`: ハッシュ計算ロジック
- `tests/test_queue.py`: `TaskEnvelope` を使用したキュー操作テスト
