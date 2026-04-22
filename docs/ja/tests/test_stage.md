# test_stage.py テスト説明

> 📅 最終更新日: 2026/04/22

## テスト目的

`TaskStage` の設定層の動作を検証します。タグの生成と無効化メカニズム、stage_mode / execution_mode の妥当性検証、プロセスモードでの pickle ガードを含みます。これらのテストは、グラフノードとしての `TaskStage` のメタデータ管理層をカバーしており、実行能力は対象外です（実行能力は `test_executor.py` でカバーされています）。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskStageConfig` | 8 | タグ生成、タグ変更、有効な stage_mode 値、有効な execution_mode 値、不正値の遮断、summary フィールド |
| `TestTaskStagePickleGuard` | 2 | lambda の遮断、通常関数の通過 |

### 主要テストケースの詳細

#### `test_stage_tag_auto_generation`
- **目的**：タグが指定されていない場合、`name` と `func_name` を含むタグが自動生成されることを検証します。
- **フォーマット**：`Stage[{func_name}]` またはカスタム名。

#### `test_stage_tag_changes_with_name`
- **目的**：`stage_name` を変更した後、古いタグが無効になり、新しいタグが新しい名前を反映することを検証します。
- **実装メカニズム**：`set_stage_name()` は `delattr(self, "_tag")` でキャッシュされたタグを削除し、次回の `get_tag()` 呼び出し時に再計算します。
- **リスク**：マルチプロセスシナリオで、親プロセスが名前を変更する前に子プロセスが古いタグを既にシリアライズしている場合、タグの不整合が発生する可能性があります。

#### `test_invalid_stage_mode`
- **目的**：不正な `stage_mode`（`"serial"` / `"thread"` / `"process"` 以外）が `StageModeError` を発生させることを検証します。

#### `test_invalid_execution_mode`
- **目的**：不正な `execution_mode`（`"serial"` / `"thread"` / `"async"` 以外）が `ExecutionModeError` を発生させることを検証します。

#### `test_summary_contains_stage_mode`
- **目的**：`get_summary()` が返す辞書に、監視ダッシュボード表示用の `stage_mode` と `execution_mode` フィールドが含まれることを検証します。
- **注意**：非シリアルモードでは、`execution_mode` にワーカー数が付加されます（例：`"thread-20"`）。

#### `test_unpickleable_lambda_raises`
- **目的**：`stage_mode="process"` の場合、lambda 関数は pickle できないため、構築時に遮断されることを検証します。
- **例外**：`PickleError`
- **意義**：ランタイムでシリアライズの失敗が発覚し、子プロセスがクラッシュすることを回避します。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow.TaskStage` | テスト対象 |
| `celestialflow.runtime.util_errors` | `ExecutionModeError`、`StageModeError`、`PickleError` |

## 発生しうる問題と注意事項

### 1. `get_tag()` のスレッド安全性
`get_tag()` は `hasattr` + 動的属性設定パターンを使用して遅延ロードキャッシュを実装しています：
```python
if hasattr(self, "_tag"):
    return str(self._tag)
self._tag = f"{self.get_name()}[{self.get_func_name()}]"
```

マルチスレッド環境では、以下が発生する可能性があります：
- スレッド A が `hasattr` をチェックし `False` を取得
- スレッド B が同時にチェックし同じく `False` を取得
- 両方のスレッドが `_tag` を作成する。結果は同一ですが、競合状態が存在します

**推奨事項**：将来スレッド安全性が必要な場合は、`@functools.cached_property` を使用するか、`__init__` で値を固定化することを検討してください。

### 2. Pickle チェックの限界
`find_unpickleable(func)` は構築時に関数が pickle 可能かどうかをチェックしますが、**クロージャ内の変数はチェックしません**。例：
```python
def make_func():
    huge_data = [0] * 1000000
    def func(x):
        return x + len(huge_data)
    return func

TaskStage(make_func(), stage_mode="process")  # 構築時は通過、シリアライズ時に失敗
```

このシナリオは現在のテストではカバーされていません。

### 3. `stage_mode="process"` と `execution_mode="async"` の組み合わせ
`TaskStage` の `set_execution_mode()` は `"serial"` / `"thread"` のみを許可しますが、`TaskExecutor` は `"async"` を許可します。継承やバリデーションのバイパスを通じて `"async"` が設定された場合、`stage_mode="process"` のマルチプロセスコンテキストで予期しない動作が発生する可能性があります。

**現在の保護**：`set_execution_mode()` は `ExecutionModeError` を発生させますが、属性の直接変更でバイパスすることは可能です。

### 4. `PickleError` テストは `stage_mode="process"` でのみトリガー
`stage_mode="serial"` では pickle チェックは実行されません。タスクが同一プロセス内で実行されるためです。つまり、以下のコードはエラーを発生させません：
```python
TaskStage(lambda x: x, stage_mode="serial")  # 通過
```

これは期待される動作ですが、ユーザーはフレームワークが lambda を完全に禁止していると誤解する可能性があります。

### 5. `test_valid_execution_mode_thread` は `max_workers` を検証していない
テストは `execution_mode` が `"thread"` に設定されることのみを検証しており、デフォルトの `max_workers` 値（20）が有効かどうか、また不正な値（0や-1など）の遮断もテストしていません。

**追加推奨**：
```python
def test_invalid_max_workers():
    with pytest.raises(ValueError):
        TaskStage(add_one, execution_mode="thread", max_workers=0)
```

## 実行方法

```bash
pytest tests/test_stage.py -v
```

すべてのテストケースは純粋な設定バリデーションであり、プロセス/スレッドの起動なし。実行時間は `< 50ms` です。

## 関連ファイル

- `src/celestialflow/stage/core_stage.py`：テスト対象の実装
- `src/celestialflow/stage/core_executor.py`：親クラス `TaskExecutor`
- `src/celestialflow/utils/util_debug.py`：`find_unpickleable`
- `tests/test_graph.py`：グラフ統合シナリオで `TaskStage` を使用
