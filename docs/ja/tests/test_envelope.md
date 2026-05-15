# test_envelope.py テスト説明

> 📅 最終更新日: 2026/05/15

## テスト目的

`TaskEnvelope`（タスクエンベロープ）のコア動作を検証します。構築、getter メソッド、遅延ハッシュ、属性の永続化、ハッシュの一貫性、メモリ最適化メカニズムを含みます。`TaskEnvelope` は CelestialFlow でキュー間でタスクを受け渡す基本単位であり、その正確性はデータフロー全体の信頼性に直接影響します。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskEnvelope` | 7 | 構築と getter、source、change_id、異なるハッシュ、同一ハッシュ、遅延ハッシュ、slots |
| `TestObjectToHash` | 4 | bytes 型を返す、SHA1 長さ、同一入力同一ハッシュ、異なる入力異なるハッシュ |

### テストケースの詳細説明

#### `test_create_and_getters`
- **目的**: コンストラクタと getter メソッドがエンベロープデータを正しく作成・読み取りできることを検証。
- **入力**: `{"key": "value", "num": 42}`、`id=100`
- **アサーション**: `get_task()` が元データを返す；`get_id()` が 100 を返す；`get_hash()` が `bytes` 型で長さ > 0 を返す。

#### `test_source_preserved`
- **目的**: `source` 属性が構築過程で失われないことを検証。
- **背景**: `source` はタスクの出所を追跡するために使用（例: `"input"`、上流 stage の tag）。

#### `test_change_id`
- **目的**: `change_id()` がエンベロープ ID を変更できることを検証（リトライシナリオで新しいトラッキング ID を生成するために使用）。

#### `test_different_tasks_different_hash`
- **目的**: 異なるペイロードが異なる `hash` 値を生成することを検証。

#### `test_same_task_same_hash`
- **目的**: 同一のペイロードが同一の `hash` 値を生成することを検証。
- **用途**: 重複チェック（`enable_duplicate_check=True`）はこの特性に依存。

#### `test_lazy_hash`
- **目的**: `hash` が構築時に `None` であり、最初の `get_hash()` 呼び出し時に初めて計算されることを検証。
- **アサーション**: 構築後 `envelope.hash is None`；`get_hash()` 呼び出し後 `envelope.hash is not None`。

#### `test_slots_memory_efficient`
- **目的**: `__slots__` が有効であり、動的属性の追加を阻止することを検証。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow.runtime.core_envelope.TaskEnvelope` | テスト対象 |
| `celestialflow.runtime.util_hash.object_to_hash` | ハッシュユーティリティ関数 |

### `TestObjectToHash` テストケースの詳細説明

#### `test_returns_bytes`
- **目的**: `object_to_hash()` が `bytes` 型を返すことを検証。

#### `test_returns_20_bytes`
- **目的**: SHA1 ダイジェストの長さが20バイトであることを検証。

#### `test_same_input_same_hash`
- **目的**: 同一入力が同一ハッシュ値を生成することを検証。

#### `test_different_input_different_hash`
- **目的**: 異なる入力が異なるハッシュ値を生成することを検証。

## 実行方法

```bash
pytest tests/test_envelope.py -v
```

## 関連ファイル

- `src/celestialflow/runtime/core_envelope.py`: テスト対象の実装
- `src/celestialflow/runtime/util_hash.py`: ハッシュ計算ロジック
- `tests/test_queue.py`: `TaskEnvelope` を使用したキュー操作テスト
