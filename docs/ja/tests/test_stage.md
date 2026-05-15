# test_stage.py テスト説明

> 📅 最終更新日: 2026/05/15

## テスト目的

`TaskStage` の設定レイヤーの動作を検証します。tag 生成と無効化メカニズム、stage_mode / execution_mode の正当性バリデーションを含みます。これらのテストはグラフノードとしての `TaskStage` のメタデータ管理層をカバーし、実行能力ではありません（実行能力は `test_executor.py` でカバー）。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskStageConfig` | 9 | tag 生成、tag 変更、stage_mode 有効値、execution_mode 有効値、不正値の遮断、summary フィールド、lambda thread モード |

### 主要テストケースの詳細

#### `test_stage_tag_auto_generation`
- **目的**: tag が指定されていない場合、`name` と `func_name` を含む自動生成 tag が生成されることを検証。
- **フォーマット**: `Stage[{func_name}]` またはカスタム name。

#### `test_stage_tag_changes_with_name`
- **目的**: `name` 変更後、古い tag が無効化され、新しい tag が新しい名前を反映することを検証。
- **実装メカニズム**: `set_name()` が `delattr(self, "_tag")` でキャッシュされた tag を削除し、次の `get_tag()` 呼び出し時に再計算。
- **リスク**: マルチスレッドシナリオで、他のスレッドがメインスレッドの name 変更前に古い tag をキャッシュしていた場合、tag の不整合が発生する可能性があります。

#### `test_invalid_stage_mode`
- **目的**: 不正な `stage_mode`（`"serial"` / `"thread"` 以外）が `StageModeError` をスローすべき。

#### `test_invalid_execution_mode`
- **目的**: 不正な `execution_mode`（`"serial"` / `"thread"` / `"async"` 以外）が `ExecutionModeError` をスローすべき。

#### `test_summary_contains_stage_mode`
- **目的**: `get_summary()` が返す辞書にモニタリングダッシュボード表示用の `stage_mode` と `execution_mode` フィールドが含まれることを検証。
- **注意**: 非 serial モードの `execution_mode` は worker 数を付加（例: `"thread-20"`）。

#### `test_lambda_allowed_in_thread`
- **目的**: `stage_mode="thread"` で lambda 関数が正常に作成できること（pickle 制限で拒否されないこと）を検証。
- **アサーション**: `get_stage_mode()` が `"thread"` を返す。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow.TaskStage` | テスト対象 |
| `celestialflow.runtime.util_errors` | `ExecutionModeError`、`StageModeError` |

## 起こりうる問題と注意事項

### 1. `get_tag()` のスレッド安全性
`get_tag()` は `hasattr` + 動的属性設定パターンで遅延読み込みキャッシュを実装：
```python
if hasattr(self, "_tag"):
    return str(self._tag)
self._tag = f"{self.get_name()}[{self.get_func_name()}]"
```

マルチスレッド環境では以下が発生する可能性があります：
- スレッド A が `hasattr` をチェックし `False` を取得
- スレッド B が同時にチェックし、同様に `False` を取得
- 両スレッドが `_tag` を作成；結果は同一ですが、競合状態が存在

**推奨**: 将来スレッド安全性が必要な場合、`@functools.cached_property` への切り替えまたは `__init__` での固定化を検討。

### 2. `test_valid_execution_mode_thread` が `max_workers` を検証していない
テストは `execution_mode` が `"thread"` に設定されていることのみ検証し、デフォルトの `max_workers` 値（20）が有効かどうか、また不正な値（例: 0、-1）の遮断はテストしていません。

**追加を推奨**：
```python
def test_invalid_max_workers():
    with pytest.raises(ValueError):
        TaskStage(add_one, execution_mode="thread", max_workers=0)
```

## 実行方法

```bash
pytest tests/test_stage.py -v
```

すべてのテストケースは純粋な設定バリデーションであり、スレッド起動なし、実行時間は `< 50ms` です。

## 関連ファイル

- `src/celestialflow/stage/core_stage.py`: テスト対象の実装
- `src/celestialflow/stage/core_executor.py`: 親クラス `TaskExecutor`
- `src/celestialflow/utils/util_debug.py`: `find_unpickleable`
- `tests/test_graph.py`: グラフ統合シナリオで `TaskStage` を使用
