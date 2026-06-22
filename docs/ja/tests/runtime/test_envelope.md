# タスクエンベロープテスト (test_envelope.py)

> 📅 最終更新日: 2026/06/22

## 役割
`celestialflow.runtime.core_envelope` モジュールの `TaskEnvelope` クラスと `object_to_hash` ハッシュユーティリティを検証し、タスクデータ、ID、ハッシュ値が伝送過程で完全性と一貫性を保つことを確認します。

## コアテスト対象
- `TaskEnvelope`: タスクデータをラップするコアコンテナ。
- `object_to_hash`: 汎用オブジェクトハッシュ計算ユーティリティ。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|-------------|---------|--------------|
| `TestTaskEnvelope` | 7 | コンストラクタ/Getter、ID 変更、ハッシュ一貫性、遅延計算、ハッシュ不可フォールバック、`__slots__` メモリ制限 |
| `TestObjectToHash` | 4 | 戻り値の型(bytes)、SHA1 固定長20バイト、同一入力の一貫性、異なる入力の差異 |

## 主要テストシナリオ

### `TestTaskEnvelope`
1. **基本属性**: コンストラクタパラメータ（task, id）が Getter メソッドで正確に復元できることを検証。
2. **ハッシュ一貫性**:
   - 同一内容のオブジェクトが同じハッシュを生成することを検証（IDが異なっていても）。
   - 異なる内容が異なるハッシュを生成することを検証。
3. **遅延計算**: ハッシュ値が初回の `get_hash()` 呼び出し時にのみ計算され、初期 `hash` 属性が `None` であることを検証。
4. **ハッシュ不可タスクのフォールバック**:
   - タスクオブジェクトが pickle できない場合、`get_hash()` が `__unhashable_task__:` をプレフィックスとする一意のフォールバックバイト列を返すことを検証。
   - 2つの異なるハッシュ不可タスクが同一のフォールバック値を再利用しないことを検証。
5. **メモリ効率**: `__slots__` 機構が有効であり、動的属性追加時に `AttributeError` がスローされることを検証。

### `TestObjectToHash`
- 戻り値が20バイトの SHA1 ダイジェストに固定されることを検証。
- 同一構造のオブジェクトが異なる呼び出し間で一貫したハッシュを生成することを検証。
- 異なるオブジェクトが異なるハッシュを生成することを検証。

## テストの重点
- **不変性の模倣**: `TaskEnvelope` は厳密には不変ではありませんが、`__slots__` によって拡張性が制限されています。
- **ハッシュの堅牢性**: `object_to_hash` が様々な Python データ型を処理できることを確認。
- **失敗時のデグレード戦略**: ハッシュ計算の失敗によって他のタスク処理フローが中断されないことを確認。
- **ID 変更**: `id` 属性の書き込み可能性を検証（`envelope.id = 999`）。フロー中にタスクを再マークするために使用されます。

## 実行方法

```bash
# 全テスト実行
pytest tests/runtime/test_envelope.py -v

# エンベロープ属性テストのみ
pytest tests/runtime/test_envelope.py -k "Envelope" -v

# object_to_hash テストのみ
pytest tests/runtime/test_envelope.py -k "ObjectToHash" -v

# ハッシュ一貫性テストのみ
pytest tests/runtime/test_envelope.py -k "hash" -v

# ハッシュ不可タスクフォールバックテストのみ
pytest tests/runtime/test_envelope.py -k "unhashable" -v

# slots メモリテストのみ
pytest tests/runtime/test_envelope.py -k "slots" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestTaskEnvelope` | ~0.1s（純粋なメモリ操作） |
| `TestObjectToHash` | < 0.1s（純粋なメモリ操作） |

## 重要な詳細
- ハッシュ計算は `id` フィールドの影響を排除し、内容が同じで ID が異なるタスクが重複として識別されることを保証します。
- pickle 不可能なタスクに対しては、テストが専用プレフィックス付きの一意なフォールバック値を返すことを検証し、例外が上方に伝播しないことを確認します。
- `test_slots_memory_efficient` は `pytest.raises(AttributeError)` を使用してメモリ最適化制限を検証します。

## 注意事項
- タスクエンベロープは、システムが異なるノード間でデータを転送する統一フォーマットです。
- 関連実装は `src/celestialflow/runtime/core_envelope.py` にあります。
