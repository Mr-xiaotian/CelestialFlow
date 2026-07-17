# demo/ デモ概要

> 📅 最終更新日: 2026/06/28

## 説明

本ディレクトリは `demo/` 配下の各種デモスクリプトの中国語説明ドキュメントを収集し、CelestialFlow のコア機能、グラフ構造の表現方法、実行モード、オブザーバー、Redis 統合、および一般的なユーティリティ関数を素早く理解できるようにします。

これらのデモは「ハンズオン体験」と「機能紹介」に重点を置いており、`bench/` のパフォーマンス比較や `tests/` の動作検証とは位置付けが異なります。

## 推奨読書順序

プロジェクトに初めて触れる方は、以下の順序で読むことを推奨します：

1. `demo_executor.md`：まず `TaskExecutor` の基本的な実行方法を理解
2. `demo_graph.md`：次に `TaskGraph` が stage をどのようにつなげて DAG を形成するかを確認
3. `demo_structure.md`：さらにチェーン、グリッド、ループ、完全グラフなどの構造化ラッパーを確認
4. `demo_observer.md`：最後に実行中の観測と進捗表示を確認

## デモモジュール概要

| ドキュメント | ソースコード | デモ目標 | 外部サービス要否 |
|------|------|---------|:---------------:|
| `demo_executor.md` | `demo/demo_executor.py` | `TaskExecutor` の serial / thread / async 3 つの実行モード | 不要 |
| `demo_observer.md` | `demo/demo_observer.py` | `TaskExecutor` に `TaskProgress` とカスタム `LoggingObserver` を登録 | 不要 |
| `demo_funnel.md` | `demo/demo_funnel.py` | タスクグラフから独立して、`BaseInlet` / `BaseSpout` でイベント収集パイプラインを構築 | 不要 |
| `demo_graph.md` | `demo/demo_graph.py` | `TaskGraph` のファンアウト/ファンイン ETL と非同期ステージ分割パイプライン | Reporter / CelestialTree（オプション） |
| `demo_stages.md` | `demo/demo_stages.py` | `TaskSplitter`、`TaskRouter` とチェーン/循環グラフ構造 | Reporter / CelestialTree（オプション） |
| `demo_structure.md` | `demo/demo_structure.py` | `TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop`、`TaskWheel`、`TaskComplete` などの定義済みトポロジ | Reporter / CelestialTree（オプション） |
| `demo_redis.md` | `demo/demo_redis.py` | 通常の `TaskStage` で Redis タスク投入、結果確認、外部タスクソースを実現 | Redis、Reporter（オプション） |
| `demo_utils.md` | `demo/demo_utils.py` | 各デモスクリプトで共有されるヘルパー関数とタスク関数 | 不要 |

> **注意**：表中の「外部サービス要否」はデフォルトエントリを直接実行する際の強い依存を指します。オプションサービスが準備できていない場合、通常はレポート送信がスキップされるだけで、デモが終了することはありません。

## ドキュメントインデックス

### 実行とタスクグラフ

| ドキュメント | 説明 |
|------|------|
| `demo_executor.md` | `TaskExecutor` のシリアル / スレッド / 非同期実行デモ |
| `demo_graph.md` | DAG タスクグラフ、ETL フロー、staged/eager スケジューリングデモ |
| `demo_structure.md` | `TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop` などの構造化グラフラッパーデモ |
| `demo_stages.md` | `TaskStage`、`TaskSplitter`、`TaskRouter` などの stage レベル機能説明 |

### 観測、パイプラインと拡張

| ドキュメント | 説明 |
|------|------|
| `demo_observer.md` | オブザーバー、進捗報告、ライフサイクルコールバックデモ |
| `demo_funnel.md` | Inlet / Spout パイプライン動作とデータフローデモ |
| `demo_redis.md` | Redis 関連統合サンプル |

### ヘルパー関数

| ドキュメント | 説明 |
|------|------|
| `demo_utils.md` | デモで共有されるヘルパー関数、入力構築、タスク関数の説明 |

## 使用方法

ほとんどのデモはプロジェクトルートから直接実行できます。例：

```bash
python demo/demo_executor.py
python demo/demo_graph.py
python demo/demo_structure.py
```

一部のデモは追加環境に依存します。例：

- Reporter サービス
- Redis サービス
- CelestialTree サービス

実行前に該当する単一ページドキュメントの「依存関係」と「実行方法」セクションを確認してください。

## 注意事項

1. デモの目的は機能の紹介であり、必ずしも最小依存や最短実行時間を追求しません。
2. 一部のサンプルは外部サービスに接続します。環境変数やサービス側の準備ができていない場合、実行時に直接失敗します。
3. フレームワークの動作の正しさを確認したい場合は、`tests/` を優先的に参照してください。パフォーマンスのトレードオフを確認したい場合は、`bench/` を優先的に参照してください。
