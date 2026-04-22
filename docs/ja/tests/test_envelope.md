# test_envelope.py テスト説明

## テスト目的

`TaskEnvelope` タスクエンベロープのコア動作を検証します。データのラップ/アンラップ、属性の永続化、ハッシュの一貫性、およびメモリ最適化メカニズムを含みます。`TaskEnvelope` は CelestialFlow においてキュー間でタスクを受け渡す基本単位であり、その正確性はデータフロー全体の信頼性に直接影響します。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskEnvelope` | 6 | wrap/unwrap、source、change_id、hash、slots |

### 詳細なテストケース説明

#### `test_wrap_unwrap`
- **目的**：`TaskEnvelope.wrap()` が任意の Python オブジェクトを正しくラップし、`unwrap()` で完全に復元できることを検証します。
- **入力**：`{"key": "value", "num": 42}`、`task_id=100`
- **アサーション**：アンラップされた task、hash、id がすべて元の値と一致すること。hash が空でない文字列であること。

#### `test_wrap_preserves_source`
- **目的**：ラップ処理中に `source` 属性が失われないことを検証します。
- **背景**：`source` はタスクの出所を追跡するために使用されます（例：`"input"`、上流ステージの tag）。

#### `test_change_id`
- **目的**：`change_id()` がエンベロープ ID を変更できることを検証します（リトライシナリオで新しいトラッキング ID を生成するために使用）。
- **注意**：変更後、古い ID は保持されません。呼び出し元が親子関係を独自に管理する必要があります。

#### `test_different_tasks_different_hash`
- **目的**：異なるペイロードが異なる `hash` 値を生成することを検証します。
- **メカニズム**：内部で `object_to_str_hash` を使用し、オブジェクトの正規化文字列表現に基づいて計算します。

#### `test_same_task_same_hash`
- **目的**：同一のペイロードが同一の `hash` 値を生成することを検証します。
- **用途**：重複チェック（`enable_duplicate_check=True`）はこの特性に依存しています。

#### `test_slots_memory_efficient`
- **目的**：`__slots__` が有効であり、動的な属性追加が阻止されることを検証します。
- **利点**：各 `TaskEnvelope` インスタンスで約50%のメモリを節約します（`__dict__` なし）。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow.runtime.core_envelope.TaskEnvelope` | テスト対象 |

## 発生しうる問題と注意事項

### 1. ハッシュ衝突
`object_to_str_hash` は文字列表現に基づいて計算します。以下のケースでは予期しない同一ハッシュが生成される可能性があります：
- `1` と `"1"`（数値と文字列）
- 異なるクラスで `__repr__` の出力が同一のオブジェクト

**推奨事項**：本番環境で `enable_duplicate_check` を使用する際は、入力タスクの型の一貫性を確保してください。

### 2. シリアライズ不可能なオブジェクトのラップ
`TaskEnvelope.wrap()` は内部で `object_to_str_hash` を呼び出します。タスクにシリアライズ不可能なオブジェクト（ファイルハンドルや lambda など）が含まれている場合、ハッシュ計算段階で失敗する可能性があります。

**調査方法**：
```python
from celestialflow.runtime.util_hash import object_to_str_hash
try:
    object_to_str_hash(your_task)
except Exception as e:
    print(f"ハッシュを計算できません: {e}")
```

### 3. `change_id` にバリデーションなし
`change_id(new_id)` は ID の一意性をチェックせず、履歴 ID チェーンも維持しません。リトライロジックで誤用すると、トレースツリーが断絶する可能性があります。

### 4. `__slots__` と継承の制限
将来 `TaskEnvelope` のサブクラスが必要になった場合、サブクラスも `__slots__` を宣言する必要があります。そうしないと、メモリ最適化の効果が失われます。

## 実行方法

```bash
pytest tests/test_envelope.py -v
```

## 関連ファイル

- `src/celestialflow/runtime/core_envelope.py`：テスト対象の実装
- `src/celestialflow/runtime/util_hash.py`：ハッシュ計算ロジック
- `tests/test_queue.py`：`TaskEnvelope` を使用したキュー操作テスト
- `tests/test_metrics.py`：ハッシュによる重複排除テスト
