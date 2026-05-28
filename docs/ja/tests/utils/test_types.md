# ランタイム型テスト (test_types.py)

> 📅 最終更新日: 2026/05/28

## 目的

`celestialflow.runtime.util_types` 内のすべてのランタイムヘルパー型（終了シグナル、カウンター、コンテキストマネージャー、イベント定数、エラーレコード）の正確性を検証します。

## コアテスト対象

| 型 | 説明 |
|----|------|
| `TerminationSignal` | `id` と `source` を持つ終了シグナル |
| `TerminationIdPool` | マージ伝播用の複数終了シグナル ID プール |
| `NoOpContext` | ロック不要シナリオのプレースホルダー実装である空コンテキストマネージャー |
| `ValueWrapper` | スレッドセーフな読み書きをサポートするロック付き値ラッパー |
| `SumCounter` | `init_value` とリセット機能を持つ複数カウンター集約アキュムレーター |
| `StageStatus` | Stage ライフサイクル列挙型（NOT_STARTED / RUNNING / STOPPED） |
| `CTreeEvent` | CTree イベント名定数 |
| `PersistedErrorRecord` | 永続化エラーレコード（frozen dataclass） |

## 主要テストシナリオ

### `TerminationSignal`
- デフォルト構築：`id=-1`、`source="input"`
- カスタム引数：`_id=42`、`source="queue"`
- 部分的な引数スキップ

### `TerminationIdPool`
- 非空リスト、空リスト、単一要素リストの構築

### `NoOpContext`
- `with` 文が正常に出入りし、変数状態が保持される
- 例外は抑制されない（`__exit__` が `None` を返す）
- `__enter__` / `__exit__` の直接呼び出し

### `ValueWrapper`
- 基本的な読み書き：`value` プロパティが正常に動作
- デフォルト値は 0
- ロック付き読み書き動作が一貫している
- `get_lock()` が提供された `Lock` または `NoOpContext` を返す
- 負の数値境界

### `SumCounter`
- 単一カウンター / 複数カウンターの累算
- `init_value` が合計に影響
- `reset()` がすべてのカウンターをゼロに（`init_value` 含む）
- 空カウンター：`value=0`
- `thread` モードの累算が正常に動作

### `StageStatus`
- 列挙値が正しい（0 / 1 / 2）
- `IntEnum` で整数と比較可能
- メンバー数は 3

### `CTreeEvent`
- タスク定数が正しい（`task.input`、`task.success`、`task.error`、`task.duplicate`）
- 終了定数が正しい（`termination.input`、`termination.merge`）
- リトライプレフィックスが `"."` で終わる

### `PersistedErrorRecord`
- 基本 / 全フィールド構築
- Frozen dataclass — 変更不可
- `__str__` が `error_repr` を返す
- `get_group_key()` が `(error_type, error_message)` タプルを返す

## 実行方法

```bash
# 全実行
pytest tests/utils/test_types.py -v

# 終了シグナルテストのみ
pytest tests/utils/test_types.py -k "termination" -v

# カウンターテストのみ
pytest tests/utils/test_types.py -k "counter or Sum or Value" -v

# 列挙型とイベントテストのみ
pytest tests/utils/test_types.py -k "status or event or Stage or CTree" -v

# エラーレコードテストのみ
pytest tests/utils/test_types.py -k "error" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|--------------|----------|
| `TestUtilTypes` | ~0.1s |

## 重要な詳細

- `NoOpContext` は Null Object パターンの実装であり、ロック不要シナリオで `ValueWrapper.get_lock()` の統一インターフェースを提供します。
- `ValueWrapper` の `get_lock()` はコンテキストマネージャー（`Lock` または `NoOpContext`）を返し、呼び出し側は統一的に `with` 文を使用します。
- `PersistedErrorRecord` は frozen dataclass であり、永続化後のエラーレコードの改ざんを防止します。
- `StageStatus` は `IntEnum` であり、整数と直接比較できます（例：`status > StageStatus.NOT_STARTED`）。

## 注意事項

- これらの型はフレームワークのコアコードで広く使用されており、その正確性はスケジューリング、重複排除、レポートなどの重要なパスに直接影響します。
- 関連実装は `src/celestialflow/runtime/util_types.py` にあります。
