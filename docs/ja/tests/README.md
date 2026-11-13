# tests/ テスト概要

> 📅 最終更新日: 2026/11/13

## 説明

本ディレクトリは `tests/` 配下の pytest テストセットの中国語説明ドキュメントを収集し、読者が異なるモジュールのカバレッジ範囲、実行方法、リグレッションリスクポイントを素早く特定できるようにします。

`demo/` とは異なり、ここでは「機能が正しいかどうか」に焦点を当てます。`bench/` とは異なり、パフォーマンスではなく、動作制約、境界ケース、プロトコル整合性に関心を置きます。

## 推奨読書順序

テストセットを初めて見る方は、以下の順序で読むことを推奨します：

1. `conftest.md`：まずテストヘルパーと共有初期化の説明を確認
2. `runtime/`：基本型、キュー、例外、スケジューリングプリミティブのカバレッジ範囲を理解
3. `graph/`：グラフ構造、タスクトポロジのコアテストを理解
4. `node/`、`funnel/`：実行スケジューリング、ディスパッチ、パイプライン関連テスト
5. `observer/`、`persist/`、`reporter/`、`ticker/`：観測、永続化、リモートレポート、タイマー
6. `assembly/`：リソースのアセンブリと起動 / 停止順序
7. `benchmark/`：ベンチマークツールとクローンツールのテスト

## ドキュメントインデックス

### トップレベルエントリ

| ドキュメント | 説明 |
|------|------|
| `conftest.md` | グローバルなテスト補助ツールと共有初期化の説明（`metrics_of`、`lifecycle_db_of`、`wait_until` など） |

### サブディレクトリ説明

| ドキュメント | 説明 |
|------|------|
| `assembly/test_run.md` | `run_graph_resources` / `run_node_resources` のリソースアセンブリ、オブザーバーの起動 / 停止、`db_path` の産出 |
| `benchmark/test_benchmark.md` / `test_clone.md` | `benchmark_graph` / `benchmark_executor` のベンチマークテストと clone ツールのテスト |
| `funnel/test_inlet.md` / `test_spout.md` | `BaseInlet.send` / `BaseSpout` の起動 / 停止と冪等性に関するテスト |
| `graph/test_graph.md` など | `TaskGraph`、タスク注入、トポロジ解析、構造エクスポートに関するテスト |
| `node/test_dispatch.md` など | `TaskDispatch` のリトライ / 終了マージ、`TaskExecutor` / `TaskSplitter` / `TaskRouter` に関するテスト |
| `observer/test_observer.md` / `test_metrics.md` | `Event` 基底クラス、`on_event` 統一エントリ、`ObserverHub.find` と指標オブザーバーに関するテスト |
| `persist/test_lifecycle.md` など | ライフサイクル記録（dataclass）、ログ、レンダリング、sqlite ユーティリティに関するテスト |
| `reporter/test_inject.md` など | リモート注入、プッシュ、状態スナップショットに関するテスト |
| `runtime/test_envelope.md` など | キュー、エンベロープ、例外、ログレベル、型などの基本ランタイムテスト |
| `ticker/test_ticker.md` など | タイマーループ、ハンドラの位相、hub のファンアウトに関するテスト |

## 使用方法

プロジェクトルートからモジュール別に実行できます：

```bash
uv run pytest tests -v
uv run pytest tests/runtime -v
uv run pytest tests/graph -v
uv run pytest tests/node -v
uv run pytest tests/observer -v
uv run pytest tests/persist -v
uv run pytest tests/reporter -v
uv run pytest tests/ticker -v
```

キーワードでフィルタすることもできます：

```bash
uv run pytest tests -k "executor or graph or reporter" -v
```

## 読み方

以下の方法でこれらのドキュメントを活用することを推奨します：

- あるモジュールが「テストされているか」を知りたい場合：まず対応するサブディレクトリの `test_*.md` を確認
- ある具体的な動作が「どのようにテストされているか」を知りたい場合：対応する `test_*.md` を確認（サブディレクトリには `__init__.md` は存在しない）
- プロトコル変更の影響範囲を特定したい場合：`graph/`、`node/`、`observer/`、`persist/`、`reporter/` のドキュメント群を優先的に確認

## 注意事項

1. 一部のテストは一時ファイル、sqlite、イベントキュー、または HTTP レポートチェーンに依存します。実行環境のジッターは実行時間に影響する可能性がありますが、アサーション結果には影響しません。
2. 本番プロトコルが変更された場合、テストドキュメントは通常 `src/`、`demo/` と共に同期更新する必要があります。
3. 現在の変更を素早く検証したいだけの場合は、変更ディレクトリに最も近いテストサブセットを優先的に実行し、常に全量テストを実行する必要はありません。
4. 本ディレクトリのサブディレクトリ（`assembly/`、`benchmark/`、`funnel/`、`graph/`、`node/`、`observer/`、`persist/`、`reporter/`、`runtime/`、`ticker/`）は**いずれも `__init__.py` を持たない**ため、対応する `__init__.md` も存在しません。
