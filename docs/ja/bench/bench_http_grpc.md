# bench_http_grpc.py ベンチマーク説明

> 📅 最終更新日: 2026/05/09

## 目的

CelestialTree イベント追跡システムの異なるトランスポートプロトコル（無効 / HTTP / gRPC）における性能オーバーヘッドを定量的に比較し、高精度追跡と最小遅延のトレードオフをユーザーに提供する。

## テスト内容

| シナリオ | 説明 |
|----------|------|
| `bench_no_ctree` | CelestialTree を完全に無効化、ベースラインとして使用 |
| `bench_http_ctree` | HTTP プロトコルで CelestialTree にイベントを上報 |
| `bench_grpc_ctree` | gRPC プロトコルで CelestialTree にイベントを上報 |

- **グラフ構造**：シンプルな `TaskSplitter → TaskStage` チェーン
- **タスク**：`no_op` 恒等関数（`range(1e4)` を処理）
- **設定**：`stage_mode="thread"`、`execution_mode="thread"`、`max_workers=50`

## 主要設定

- `ctree_host`、`ctree_http_port`、`ctree_grpc_port` は `.env` から読み込み

## 発生し得る問題

1. **CelestialTree サービス未起動**：HTTP/gRPC シナリオでサーバーが利用不可の場合、テストは接続例外を直接スローする。
2. **ネットワーク遅延が結果を支配**：タスクが `no_op`（ほぼゼロ計算）のため、測定された時間差はほぼ完全にイベント上報のネットワーク RTT に由来し、CPU 集約型シナリオでの実際の比率を反映しない。
3. **HTTP 接続の非再利用**：現在の実装は各イベント上報で新しい HTTP 接続を作成する可能性がある。コネクションプール（例：`requests.Session`）を使用すれば HTTP 性能は大幅に向上する。
4. **gRPC コールドスタート**：最初の gRPC 呼び出しは TLS/ハンドシェイクネゴシエーションが必要で、短いタスクでは高い遅延として現れる可能性がある。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、TaskSplitter → TaskStage チェーン、`range(1e4)` を処理
> 外部サービス：ローカル CelestialTree（HTTP + gRPC）

| シナリオ | 所要時間 | ベースライン比オーバーヘッド |
|----------|----------|---------------------------|
| **no ctree**（ベースライン） | 4.14s | — |
| **http ctree** | 9.46s | +129% |
| **grpc ctree** | 9.25s | +124% |

**主要な結論**：
- HTTP と gRPC はこのシナリオでほぼ同じ性能（差異 < 2%）
- イベント追跡により合計所要時間が約 **2.3 倍**増加（4.14s → 9.3s）
- タスクが `no_op`（ゼロ計算）のため、オーバーヘッド比率が増幅されている。CPU 集約型タスクではこの比率は大幅に低下する
- gRPC は明確な優位性を示さなかった。おそらくローカルネットワーク RTT が非常に低く、HTTP のコネクション再利用により差が縮まっている

## 実行方法

```bash
python bench/bench_http_grpc.py
```

## 依存関係

- `celestialflow`（`TaskChain`、`TaskSplitter`、`TaskStage`）
- `python-dotenv`
- 外部サービス：CelestialTree（HTTP ポート + gRPC ポート）
