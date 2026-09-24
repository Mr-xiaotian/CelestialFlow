# tests/runtime/test_metrics.py

> 📅 最終更新日: 2026/09/24

## 役割
`celestialflow.runtime.core_metrics` の `TaskMetrics` クラスを検証し、タスク実行中の各種統計指標（入力、成功、失敗、重複、保留中）が正確に計算されることを確認し、上流/下流のバインドカウンタ、リトライ可能例外の設定、ビジーウォールクロック所要時間（busy time）の累積口径をカバーします。

## コアテスト対象
- `TaskMetrics`: 単一ノード（Stage）のタスクカウント、上流/下流のバインドカウント、リトライ可能例外とビジー所要時間の追跡を担当。
- `ValueWrapper`: 上流/下流カウント用のスレッドセーフラッパー。テストでは `ValueWrapper` を直接使って上流/下流カウンタを模擬。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestTaskMetricsBasic` | 9 | 初期カウント、外部入力の累積、外部/上流入力の分割、成功/失敗/重複の累積、`processed`/`pending` の数式、完了判定 |
| `TestTaskMetricsBinding` | 5 | 上流カウンタの総数への算入、`connect_to` によるカウンタ共有、未登録下流で `KeyError`、上流/下流カウントマップのクエリ |
| `TestTaskMetricsRetryExceptions` | 2 | デフォルトのリトライ可能例外が空、例外型の動的追加 |
| `TestTaskMetricsElapsed` | 3 | ビジー所要時間の初期値 0、実行期間中のみ累積、並行の重なりはウォールクロックで1回のみ計上 |
| **合計** | **19** | |

## 主要テストシナリオ

### 基本カウント (`TestTaskMetricsBasic`)
1. **初期状態** (`test_initial_counts`): 新規 `TaskMetrics` では `tasks_input/succeeded/failed/duplicated/processed/pending` がすべて 0、`get_external_input_count()`、`get_upstream_input_count()` が 0、上流/下流カウントマップが空の辞書。
2. **外部入力の累積** (`test_add_external_input_count`): `add_external_input_count(5)` の後、外部入力が 5、上流入力が 0、`get_input_count()` と `tasks_input` がいずれも 5。
3. **入力の分割** (`test_input_count_split_external_and_upstream`): `set_upstream_counter` で 2 つの上流を登録し、それぞれ累積した後、外部 3、上流 6、合計 9 を検証。
4. **成功/失敗/重複の累積**: `add_success_count`、`add_fail_count`、`add_duplicate_count` がそれぞれ対応する Getter と `get_counts()` のキーを更新。
5. **数式検証** (`test_processed_equals_sum`): `tasks_processed = succeeded + failed + duplicated`、`tasks_pending = input - processed` を検証。
6. **完了判定** (`test_is_tasks_finished_true` / `_false`): `pending` が 0 のとき `True` を返し、そうでなければ `False` を返す。

### 上流/下流バインド (`TestTaskMetricsBinding`)
- `test_upstream_counter_adds_to_task_count`: 上流の `ValueWrapper` を 3 増やすと、現在のノードの `get_input_count()` と `get_upstream_input_count()` がいずれも 3、外部入力は 0。
- `test_shared_binding_counter`: `prev.set_downstream_counter` と `curr.set_upstream_counter` に同一の `ValueWrapper` を渡し、`prev.add_downstream_count` の後 `curr.get_input_count()` がその増分を反映。
- `test_add_downstream_count_missing_target_raises`: 未登録名に対して `add_downstream_count` を呼ぶと `KeyError` をスロー。
- `test_get_upstream_counts` / `test_get_downstream_counts`: `{名前: 数量}` マッピングを返すことを検証。

### リトライ設定 (`TestTaskMetricsRetryExceptions`)
- デフォルト `retry_exceptions == ()`。
- `set_retry_exceptions(ValueError, RuntimeError)` の後、両方の例外が `retry_exceptions` タプルに現れる。

### ビジー所要時間 (`TestTaskMetricsElapsed`)
手動で進められる `_FakeClock` で `celestialflow.runtime.core_metrics.time.perf_counter` を差し替えます：
1. **初期値 0** (`test_elapsed_is_zero_without_tasks`): タスク実行がない場合 `get_elapsed() == 0.0`。
2. **ビジー期間のみ累積** (`test_elapsed_accumulates_only_while_busy`): `begin_task()` 後、未クローズの時間片も算入され（2.0s）；`end_task()` 後に 5s アイドルしても増加しない。
3. **並行の重なりは1回計上** (`test_elapsed_counts_overlapping_tasks_once`): 2 回の `begin_task()` が重なる期間はウォールクロックで1回計上され、各タスクの合計が 5s でも 3s だけ記録；終了後のアイドルでは増加しない。

## テストの重点
- **指標の保存則**: `tasks_input` と `tasks_processed + tasks_pending` が一致し続ける。
- **バインド共有**: 上流/下流が同一の `ValueWrapper` インスタンスを通じてカウントを共有し、`connect_to` のセマンティクスがこれによって保証される。
- **所要時間の口径**: ビジー所要時間はノードのウォールクロック時間で累積され、並行タスクの重複区間は1回のみ計上される。

## 実行方法

```bash
# 全部実行
pytest tests/runtime/test_metrics.py -v

# 基本カウントテストのみ実行
pytest tests/runtime/test_metrics.py -k "count" -v

# 上流/下流バインドテストのみ実行
pytest tests/runtime/test_metrics.py -k "binding or upstream or downstream" -v

# ビジー所要時間テストのみ実行
pytest tests/runtime/test_metrics.py -k "elapsed" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|------|
| `TestTaskMetricsBasic` / `TestTaskMetricsBinding` / `TestTaskMetricsRetryExceptions` | ~0.1s（純粋なロジック演算） |
| `TestTaskMetricsElapsed` | < 0.1s（フェイククロック差し替え、実待機なし） |

## 重要な詳細
- 統計指標は Dashboard 表示とグラフ実行終了判定のデータソースです。
- `get_elapsed()` は `_busy_since` が非 None の場合、現在未クローズの時間片も併せて算入します。
- `_FakeClock` は `monkeypatch.setattr` で `core_metrics.time.perf_counter` を置き換え、テストで実待機を発生させません。

## 注意事項
- 統計指標の正確性は `TaskGraph` の自動クローズ判定に直接影響します。
- 関連実装は `src/celestialflow/runtime/core_metrics.py` にあります。
