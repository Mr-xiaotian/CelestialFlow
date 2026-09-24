# tests/runtime/test_envelope.py

> 📅 最終更新日: 2026/09/24

## 役割
`celestialflow.runtime.core_envelope` モジュールの `TaskEnvelope` クラスを検証し、タスクデータと ID がエンベロープによって正しく保存され Getter で復元できること、同時に `__slots__` のメモリ制約が有効であることを確認します。

## コアテスト対象
- `TaskEnvelope`: タスクデータとタスク ID をラップするコアコンテナ。`__slots__ = ("_id", "_task")` でインスタンス属性を制限。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestTaskEnvelope` | 3 | コンストラクタ/Getter、`get_id` クエリ、`__slots__` メモリ制限 |

## 主要テストシナリオ

### `TestTaskEnvelope`
1. **構築と復元** (`test_create_and_getters`): 辞書タスク `{"key": "value", "num": 42}` と `id=100` でエンベロープを構築し、`get_task()` が元のタスクを返し、`get_id()` が 100 を返すことを検証。
2. **ID クエリ** (`test_get_id`): 文字列タスク `"hello"` と `id=1` で構築し、`get_id()` が 1 を返すことを検証。
3. **メモリ効率** (`test_slots_memory_efficient`): `__slots__` 機構が有効であり、インスタンスに動的に `extra_attr` を追加すると `AttributeError` がスローされることを検証。

## テストの重点
- **データ完全性**: エンベロープはタスクオブジェクトと ID を無損失で保存しなければならない。
- **拡張不可性**: `__slots__` によって動的属性を阻止し、メモリ使用量を制御可能にする。

## 実行方法

```bash
# 全部実行
pytest tests/runtime/test_envelope.py -v

# Getter 関連テストのみ実行
pytest tests/runtime/test_envelope.py -k "get_id or getters" -v

# slots メモリテストのみ実行
pytest tests/runtime/test_envelope.py -k "slots" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestTaskEnvelope` | < 0.1s（純粋なメモリ操作） |

## 重要な詳細
- `test_create_and_getters` は非スカラー（辞書）タスクを使用し、エンベロープが任意のオブジェクト型をそのまま保存できることを検証。
- `test_slots_memory_efficient` は `pytest.raises(AttributeError)` を使用してメモリ最適化制限を検証。

## 注意事項
- タスクエンベロープは、システムが異なるノード間でデータを転送する統一フォーマットです。
- 関連実装は `src/celestialflow/runtime/core_envelope.py` にあります。
