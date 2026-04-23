# bench_http_grpc.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目標

CelestialTree イベントトレーシングシステムの異なるトランスポートプロトコル（無効 / HTTP / gRPC）における性能オーバーヘッドを定量的に比較し、高精度トレーシングと最小遅延のトレードオフをユーザーが判断できるようにします。

## テスト内容

| シナリオ | 説明 |
|---------|------|
| `bench_no_ctree` | CelestialTree を完全に無効化、ベースラインとして使用 |
| `bench_http_ctree` | HTTP プロトコルで CelestialTree にイベントを報告 |
| `bench_grpc_ctree` | gRPC プロトコルで CelestialTree にイベントを報告 |

- **グラフ構造**：シンプルな `TaskSplitter -> TaskStage` チェーン
- **タスク**：`no_op` 恒等関数（`range(1e4)` を処理）
- **設定**：`stage_mode="process"`、`execution_mode="thread"`、`max_workers=50`

## 主要設定

- `ctree_host`、`ctree_http_port`、`ctree_grpc_port` は `.env` から読み込みます

## 発生しうる問題

1. **CelestialTree サービス未起動**：HTTP/gRPC シナリオでサーバーが利用できない場合、テストは直接接続例外をスローします。
2. **ネットワーク遅延が結果を支配**：タスクが `no_op`（ほぼゼロの計算量）のため、計測された時間差はほぼ完全にイベント報告のネットワーク RTT によるものであり、CPU 集約型シナリオでの実際の割合を反映していません。
3. **HTTP 接続の非再利用**：現在の実装では各イベント報告で新しい HTTP 接続を作成する場合があります。コネクションプール（例：`requests.Session`）を使用すれば HTTP 性能が大幅に向上します。
4. **gRPC コールドスタート**：最初の gRPC 呼び出しには TLS/ハンドシェイクネゴシエーションが必要であり、短いタスクでは高い遅延として現れる場合があります。

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10、TaskSplitter -> TaskStage チェーン、`range(1e4)` を処理
> 外部サービス：ローカル CelestialTree（HTTP + gRPC）

| シナリオ | 所要時間 | ベースライン比オーバーヘッド |
|---------|----------|--------------------------|
| **no ctree**（ベースライン） | 4.14s | — |
| **http ctree** | 9.46s | +129% |
| **grpc ctree** | 9.25s | +124% |

**主要な結論**：
- HTTP と gRPC はこのシナリオではほぼ同等の性能です（差 < 2%）
- イベントトレーシングは合計所要時間を約 **2.3x** 増加させます（4.14s -> 9.3s）
- タスクが `no_op`（ゼロ計算）のため、オーバーヘッド比率が増幅されています。CPU 集約型タスクではこの比率は大幅に低下します
- gRPC は明確な優位性を示しませんでした。これはおそらくローカルネットワーク RTT が極めて低く、HTTP 接続再利用後の差が縮小するためです

## 実行方法

```bash
python bench/bench_http_grpc.py
```

## 依存関係

- `celestialflow`（`TaskChain`、`TaskSplitter`、`TaskStage`）
- `python-dotenv`
- 外部サービス：CelestialTree（HTTP ポート + gRPC ポート）
