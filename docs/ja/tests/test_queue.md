# test_queue.py テスト説明

> 📅 最終更新日: 2026/04/22

## テスト目的

`TaskInQueue`（タスク入力キュー）と `TaskOutQueue`（タスク出力キュー）のコア動作を検証します。タスクエンベロープのエンキュー/デキュー、終了信号のマージロジック、例外ソース検証、キュードレイン、ブロードキャスト/ターゲット送信、動的キュー管理を含みます。この2つのクラスは CelestialFlow のデータフローエンジンのパイプライン層であり、その信頼性はグラフスケジューリングの正確性を直接決定します。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskInQueue` | 5 | put/get、終了信号直接終了、複数ソースマージ、不明ソースエラー、drain |
| `TestTaskOutQueue` | 4 | ブロードキャスト、ターゲット送信、動的キュー追加、重複タグ検証 |

### 主要テストケースの詳細

#### `test_put_and_get_task`
- **目的**: `TaskEnvelope` がデータ損失なく正しくエンキュー・デキューできることを検証。
- **メカニズム**: 内部では Python 標準ライブラリの `queue.Queue`（スレッドセーフ）を使用。

#### `test_input_termination_direct_exit`
- **目的**: `source == "input"` の場合、終了信号は他の上流を待たずに即座に `TerminationIdPool` を返すべき。
- **設計**: 外部（例: ユーザーが Web インターフェース経由）から注入された終了信号をシミュレーション。

#### `test_multi_source_termination_merge`
- **目的**: 複数上流 DAG シナリオで、すべての上流が終了信号を送信してから1つの `TerminationIdPool` にマージされることを検証。
- **設計**: キュータグは `["src_a", "src_b"]`；2つの終了信号を順次注入。
- **アサーション**: マージ後の `ids` が `[10, 20]` を含む。
- **注意**: 最初の注入後、`get()` は2番目の注入が返されるまでブロックします。これはフレームワークの staged/eager 終了セマンティクスのコアメカニズムです。

#### `test_unknown_source_termination_raises`
- **目的**: `queue_tags` に含まれないソースからの終了信号が `ValueError` をスローすべき。
- **セキュリティ上の意義**: 悪意のあるまたは誤った上流ノードが偽の終了信号を送信し、早期シャットダウンを引き起こすことを防止。

#### `test_drain_returns_remaining_tasks`
- **目的**: `drain()` がノンブロッキングでキューを空にし、残りのすべての `TaskEnvelope` を返し、終了信号は記録するが返さないべき。
- **使用場面**: グラフ実行完了後のリソースクリーンアップフェーズ、未消費タスクを収集して失敗ログに永続化。

#### `test_put_broadcasts_to_all`
- **目的**: `TaskOutQueue.put()` が登録されたすべての出力キューに同じエンベロープをブロードキャスト。
- **使用場面**: `TaskGraph` のファンアウト（fan-out）エッジ。

#### `test_put_target_single_queue`
- **目的**: `put_target(envelope, tag="b")` が指定タグのキューにのみ送信。
- **使用場面**: `TaskRouter` のルート分配。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow.runtime.core_queue` | `TaskInQueue`、`TaskOutQueue` |
| `celestialflow.persistence.core_log` | `LogSpout`、`LogInlet`（fixture 依存） |

## 起こりうる問題と注意事項

### 1. `get()` のブロッキング性
`TaskInQueue.get()` はブロッキング呼び出しです。ユニットテストで終了信号ロジックにバグがある場合（例: 特定の上流からの終了信号を永遠に受信できない）、テストは pytest がタイムアウトするまでハングします。

**現在のタイムアウト保護**: pytest のデフォルト関数タイムアウトは外部設定（例: `pytest-timeout` プラグイン）で制御されます。CI に `pytest-timeout` をインストールすることを推奨：
```bash
pip install pytest-timeout
pytest tests/test_queue.py --timeout=10
```

### 2. `drain` と `get` の競合状態
`drain()` は `queue.get_nowait()` を使用してノンブロッキングで空にします。`drain()` 実行中に別のスレッド/プロセスが同時に `put()` を呼び出すと、以下が発生する可能性があります：
- `drain()` 完了後にわずかなタスクが残る
- 終了信号が完全に記録されない

**推奨**: すべての上流が停止を確認し、新しいデータが生成されなくなった場合にのみ `drain()` を呼び出してください（フレームワークは `_finalize_nodes` でこの条件を保証します）。

### 3. `LogSpout` のファイル副作用
テスト fixture は `LogSpout` を起動し、`logs/task_logger(YYYY-MM-DD).log` ファイルを作成します。テストは書き込みを減らすために `log_level="ERROR"` を使用しますが、空のログファイルが生成される可能性があります。

**クリーンアップ推奨**: CI の `after_script` でログをクリーンアップ：
```bash
rm -rf logs/
```

### 4. `queue_tags` の順序依存性
`TaskInQueue._merge_termination()` は `queue_tags` の順序で ID リストをマージします。現在のテストは `sorted()` で比較していますが、本番コードでの終了 ID の順序は CelestialTree でのプロヴェナンスツリー表示に影響する可能性があります。

### 5. 非同期キューがカバーされていない
現在のテストは同期キュー（`queue.Queue`）のみカバーしています。`TaskInQueue` と `TaskOutQueue` は `asyncio.Queue` もサポートしていますが、以下のパスは未テストです：
- `put_async()` / `get_async()`
- `put_channel_async()`

**追加を推奨**：
```python
@pytest.mark.asyncio
async def test_put_async():
    q = asyncio.Queue()
    in_queue = TaskInQueue(q, ...)
    await in_queue.put_async(envelope)
```

### 6. `TaskOutQueue` の `put_target` 例外
`tag` が `_tag_to_idx` に存在しない場合、`put_target()` はカスタム例外ではなく `KeyError` をスローします。この失敗パスは現在テストでカバーされていません。

## 実行方法

```bash
pytest tests/test_queue.py -v
```

すべてのテストケースの実行時間は `< 500ms` です。

## 関連ファイル

- `src/celestialflow/runtime/core_queue.py`: テスト対象の実装
- `src/celestialflow/runtime/core_envelope.py`: `TaskEnvelope`
- `src/celestialflow/runtime/util_types.py`: `TerminationSignal`、`TerminationIdPool`
- `tests/test_graph.py`: グラフレベルでのキュー統合を検証
