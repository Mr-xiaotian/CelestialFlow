# bench/ ベンチマーク概要

> 📅 最終更新日: 2026/06/18

## 説明

本ディレクトリは `CelestialFlow` プロジェクトの各種 benchmark ドキュメントを収集し、実行モード、グラフスケジューリング、永続化、キュー、ハッシュ、ロックオーバーヘッド、ネットワークリクエスト、および Python 3.14 GIL / No-GIL 比較などのトピックをカバーします。

これらの benchmark の主な用途は次の3つです：

- フレームワーク設計のトレードオフに定量的根拠を提供する
- ユーザーがタスクタイプに応じて適切な実行モードを選択できるようにする
- 異なる実装戦略におけるスループット、レイテンシ、リソースオーバーヘッドの差異を記録する

## 推奨読書順序

プロジェクトのパフォーマンス特性の全体像を素早く把握したい場合は、以下の順序で読むことを推奨します：

1. `bench_execution_mode.md`：まず単一エグゼキュータの `serial / thread / async` での差異を確認
2. `bench_graph_mode.md`：次にタスクグラフの異なる `stage_mode × execution_mode` の組み合わせパフォーマンスを確認
3. `bench_gil_vs_nogil.md`：最後に Python 3.14 free-threading が CelestialFlow に与える影響を確認

## ドキュメントインデックス

### 実行モデルとスケジューリング

| ドキュメント | 説明 |
|------|------|
| `bench_execution_mode.md` | `TaskExecutor` の `serial / thread / async` でのパフォーマンス比較 |
| `bench_graph_mode.md` | `TaskGraph` の異なる `stage_mode × execution_mode` 組み合わせでのパフォーマンス比較 |
| `bench_gil_vs_nogil.md` | Python 3.14 GIL と No-GIL 環境での CelestialFlow 実行差異 |

### ネットワークと外部サービス

| ドキュメント | 説明 |
|------|------|
| `bench_http_grpc.md` | CelestialTree オフ / HTTP / gRPC の3つのトレースモードのオーバーヘッド比較 |
| `bench_requests.md` | Web API リクエストベンチマーク |

### 永続化とキュー

| ドキュメント | 説明 |
|------|------|
| `bench_persistence_spout.md` | 永続化 spout のログ / fallback 書き込みパフォーマンス |
| `bench_queue.md` | キュー実装ベンチマーク |
| `bench_ipc_queue.md` | プロセス間キュー通信オーバーヘッドテスト |
| `bench_mpqueue_vs_shared_memory.md` | `multiprocessing.Queue` と共有メモリ方式の比較 |

### データ構造と基本オーバーヘッド

| ドキュメント | 説明 |
|------|------|
| `bench_lock_overhead.md` | ロック競合と同期オーバーヘッド |
| `bench_datastructures.md` | 一般的なデータ構造とクロスプロセス構造のパフォーマンスベースライン |
| `bench_hash.md` | `make_hashable` などのハッシュ関連メソッド比較 |
| `bench_hash_container.md` | コンテナクラスオブジェクトのハッシュパフォーマンス比較 |
| `bench_hash_memory.md` | ハッシュ関連実装のメモリ使用量テスト |
| `bench_futures_memory.md` | futures バッチシナリオのメモリオーバーヘッド |
| `bench_tqdm.md` | プログレスバー出力オーバーヘッドテスト |
| `bench_utils.md` | benchmark 補助統計ツールの説明 |

## 使用方法

ほとんどの benchmark はプロジェクトルートから直接実行できます。例：

```bash
python bench/bench_execution_mode.py
python bench/bench_graph_mode.py
python bench/bench_gil_vs_nogil.py
```

このうち `bench_gil_vs_nogil.py` は GIL と No-GIL インタープリタでそれぞれ1回ずつ実行する必要があります。具体的な実行方法は以下を参照してください：

- `bench_gil_vs_nogil.md`

## 注意事項

1. 一部の benchmark は Reporter、CelestialTree、特定の HTTP インターフェースなどの外部サービスに依存します。
2. 一部の benchmark の実行時間はローカル負荷、バックグラウンドプロセス、電源ポリシー、ネットワーク状態に敏感なため、少なくとも3回の繰り返し実行を推奨します。
3. benchmark の結論はタスクタイプに応じて理解すべきであり、あるシナリオの最適解をすべてのワークロードにそのまま一般化できません。
