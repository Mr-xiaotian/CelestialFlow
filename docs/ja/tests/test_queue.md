# test_queue.py テスト説明

## テスト目的

`TaskInQueue`（タスク入力キュー）と `TaskOutQueue`（タスク出力キュー）のコア動作を検証します。タスクエンベロープのエンキュー/デキュー、終了シグナルのマージロジック、不正ソースの検証、キューのドレイン、ブロードキャスト/ターゲット送信、および動的キュー管理を含みます。これら2つのクラスは CelestialFlow のデータフローエンジンのパイプライン層を構成し、その信頼性がグラフスケジューリングの正確性を直接決定します。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskInQueue` | 5 | put/get、終了シグナル直接終了、マルチソースマージ、不明ソースエラー、drain |
| `TestTaskOutQueue` | 4 | ブロードキャスト、ターゲット送信、動的キュー追加、重複タグ検証 |

### 主要テストケースの詳細

#### `test_put_and_get_task`
- **目的**：`TaskEnvelope` が正しくエンキューおよびデキューでき、データが失われないことを検証します。
- **メカニズム**：内部で Python 標準ライブラリの `queue.Queue`（スレッドセーフ）を使用します。

#### `test_input_termination_direct_exit`
- **目的**：`source == "input"` の場合、終了シグナルは他の上流を待たずに即座に `TerminationIdPool` を返すことを検証します。
- **設計**：外部（例：ユーザーが Web インターフェース経由）から直接注入された終了シグナルをシミュレートします。

#### `test_multi_source_termination_merge`
- **目的**：マルチ上流 DAG シナリオで、すべての上流が終了シグナルを送信した後にのみ、マージされた `TerminationIdPool` が返されることを検証します。
- **設計**：キュータグは `["src_a", "src_b"]` で、2つの終了シグナルを順次注入します。
- **アサーション**：マージされた `ids` に `[10, 20]` が含まれること。
- **注意**：最初の注入後、`get()` は2回目の注入が完了するまでブロッキング待機します。これはフレームワークの staged/eager 終了セマンティクスの中核です。

#### `test_unknown_source_termination_raises`
- **目的**：`queue_tags` に含まれないソースからの終了シグナルが `ValueError` を発生させることを検証します。
- **セキュリティ上の意義**：悪意のあるまたは誤った上流ノードが偽造終了シグナルを送信して早期シャットダウンを引き起こすことを防止します。

#### `test_drain_returns_remaining_tasks`
- **目的**：`drain()` がノンブロッキングでキューを空にし、残りのすべての `TaskEnvelope` を返し、終了シグナルは記録するが返さないことを検証します。
- **ユースケース**：グラフ実行終了後のリソースクリーンアップフェーズで、未消費タスクを収集して失敗ログに永続化します。

#### `test_put_broadcasts_to_all`
- **目的**：`TaskOutQueue.put()` がすべての登録済み出力キューに同じエンベロープをブロードキャストすることを検証します。
- **ユースケース**：`TaskGraph` のファンアウト（fan-out）エッジ。

#### `test_put_target_single_queue`
- **目的**：`put_target(envelope, tag="b")` が指定されたタグのキューにのみ送信することを検証します。
- **ユースケース**：`TaskRouter` のルーティング分配。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow.runtime.core_queue` | `TaskInQueue`、`TaskOutQueue` |
| `celestialflow.persistence.core_log` | `LogSpout`、`LogInlet`（fixture 依存） |

## 発生しうる問題と注意事項

### 1. `get()` のブロッキング性
`TaskInQueue.get()` はブロッキング呼び出しです。単体テストで終了シグナルロジックにバグがある場合（例：上流からの終了シグナルを永遠に待ち続ける）、テストは pytest がタイムアウトするまでハングします。

**現在のタイムアウト保護**：pytest の関数タイムアウトは外部設定（`pytest-timeout` プラグインなど）で制御されます。CI では `pytest-timeout` のインストールを推奨します：
```bash
pip install pytest-timeout
pytest tests/test_queue.py --timeout=10
```

### 2. `drain` と `get` の競合状態
`drain()` は `queue.get_nowait()` を使用してノンブロッキングで空にします。`drain()` の実行中に別のスレッド/プロセスが `put()` を呼び出している場合、以下が発生する可能性があります：
- `drain()` 完了後にわずかなタスクが残留する
- 終了シグナルが完全に記録されない

**推奨事項**：`drain()` はすべての上流が停止を確認し、新しいデータが入ってこなくなった後にのみ呼び出してください（フレームワークは `_finalize_nodes` でこの条件を保証します）。

### 3. `LogSpout` のファイル副作用
テスト fixture が `LogSpout` を起動し、`logs/task_logger(YYYY-MM-DD).log` ファイルが作成されます。テストでは書き込みを最小限にするため `log_level="ERROR"` を使用していますが、空のログファイルが生成される可能性があります。

**クリーンアップの推奨**：CI の `after_script` でログをクリーンアップしてください：
```bash
rm -rf logs/
```

### 4. `queue_tags` の順序感度
`TaskInQueue._merge_termination()` は `queue_tags` の順序に従って ID リストをマージします。現在のテストでは比較に `sorted()` を使用していますが、本番コードでの終了 ID の順序は CelestialTree のプロベナンスツリー表示に影響する可能性があります。

### 5. 非同期キュー未カバー
現在のテストは同期キュー（`queue.Queue`）のみをカバーしています。`TaskInQueue` と `TaskOutQueue` は `asyncio.Queue` もサポートしていますが、以下のパスはテストされていません：
- `put_async()` / `get_async()`
- `put_channel_async()`

**追加推奨**：
```python
@pytest.mark.asyncio
async def test_put_async():
    q = asyncio.Queue()
    in_queue = TaskInQueue(q, ...)
    await in_queue.put_async(envelope)
```

### 6. `TaskOutQueue` の `put_target` 例外
`tag` が `_tag_to_idx` に存在しない場合、`put_target()` はカスタム例外ではなく `KeyError` を発生させます。この失敗パスは現在テストでカバーされていません。

## 実行方法

```bash
pytest tests/test_queue.py -v
```

すべてのテストケースの実行時間は `< 500ms` です。

## 関連ファイル

- `src/celestialflow/runtime/core_queue.py`：テスト対象の実装
- `src/celestialflow/runtime/core_envelope.py`：`TaskEnvelope`
- `src/celestialflow/runtime/util_types.py`：`TerminationSignal`、`TerminationIdPool`
- `tests/test_graph.py`：グラフレベルでのキュー統合の検証
