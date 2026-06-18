# bench_http_grpc.py ベンチマーク説明

> 📅 最終更新日: 2026/06/18

## 目的

CelestialTree イベント追跡システムの異なる転送プロトコル（無効 / HTTP / gRPC）におけるパフォーマンスオーバーヘッドを定量比較し、高精度追跡と最小遅延のトレードオフ判断を支援する。

## テスト内容

| シナリオ | 説明 |
|----------|------|
| `bench_no_ctree` | CelestialTree を完全に無効化、ベースラインとして使用 |
| `bench_http_ctree` | HTTP プロトコルで CelestialTree にイベントを報告 |
| `bench_grpc_ctree` | gRPC プロトコルで CelestialTree にイベントを報告 |

- **グラフ構造**：`TaskSplitter → TaskStage` のシンプルなチェーン
- **タスク**：`no_op` 恒等関数（`range(1e4)` を処理）
- **設定**：`stage_mode="thread"`、`execution_mode="thread"`、`max_workers=50`

## 主要設定

- `ctree_host`、`ctree_http_port`、`ctree_grpc_port` は `.env` から読み込み

## 発生し得る問題

1. **CelestialTree サービス未起動**：HTTP/gRPC シナリオでサービス側が利用不可の場合、テストは直接接続例外をスローする。
2. **ネットワーク遅延が結果を支配**：タスクが `no_op`（ほぼゼロ計算）であるため、測定された時間差はほぼ完全にイベント報告のネットワーク RTT に由来し、CPU 集約型シナリオでの実際の比率を反映しない。
3. **HTTP 接続が再利用されない**：現在の実装では各イベント報告が新しい HTTP 接続を確立する可能性がある。接続プール（`requests.Session` 等）を使用すれば HTTP 性能は顕著に向上する。
4. **gRPC コールドスタート**：gRPC の初回呼び出しは TLS/ハンドシェイクネゴシエーションが必要で、短時間タスクでは高い遅延として現れる可能性がある。

## ベンチマーク結果（実測）

### 履歴結果 - ローカル CelestialTree（日時未記録）

> 環境：Windows、Python 3.10、TaskSplitter → TaskStage チェーン、`range(1e4)` を処理
> 外部サービス：ローカル CelestialTree（HTTP + gRPC）

| シナリオ | 所要時間 | ベースライン比 overhead |
|------|------|------------------|
| **no ctree**（ベースライン） | 4.14s | — |
| **http ctree** | 9.46s | +129% |
| **grpc ctree** | 9.25s | +124% |

**主要な結論**：
- HTTP と gRPC はこのシナリオでほぼ同等の性能（差 < 2%）
- イベント追跡により合計所要時間が約 **2.3x** 増加（4.14s → 9.3s）
- タスクが `no_op`（ゼロ計算）であるため overhead 比率が増幅されている。CPU 集約型タスクではこの比率は顕著に低下する
- gRPC に顕著な優位性が見られないのは、ローカルネットワーク RTT が極めて低く、HTTP 接続再利用後の差が縮小したためと考えられる

### 2026/06/16 - 今回未再実行（外部サービス利用不可）

> 説明：`127.0.0.1:7777` と `127.0.0.1:7778` を確認したところ、CelestialTree の HTTP / gRPC ポートはいずれも利用不可

- `bench_http_grpc.py` はローカル CelestialTree サービスに依存するため、今回新しい所要時間データは書き込まれなかった
- 履歴結果は引き続きプロトコルオーバーヘッドのオーダー参考として使用可能だが、現在のバージョンの比較可能なデータを得るには、対応する HTTP と gRPC サービスを先に起動する必要がある

## 実行方法

```bash
python bench/bench_http_grpc.py
```

## パラメータ調整

### 特定転送モードのみをテスト

`main()` 内で不要なモードをコメントアウトできる：

```python
def main():
    bench_no_ctree()       # ベースラインのみテスト
    # bench_http_ctree()   # HTTP をスキップ
    # bench_grpc_ctree()   # gRPC をスキップ
```

### タスク規模の調整

`TaskSplitter` が `range(1e4)` を展開するため、より大きくまたは小さく変更できる：

```python
# 素早く検証（少量タスク）
range(100)

# 高負荷テスト
range(100_000)
```

### 並行ワーカー数の調整

```python
# 関数内部で変更
max_workers=20   # 並行数を削減
# max_workers=100  # 並行数を増加
```

修正後に実行：

```bash
python bench/bench_http_grpc.py
```

## 依存関係

- `celestialflow`（`TaskChain`、`TaskSplitter`、`TaskStage`）
- `celestialtree`（追加インストールが必要。ソースリポジトリでは `uv sync --group dev` で取得可能）
- `python-dotenv`
- 外部サービス：CelestialTree（HTTP ポート + gRPC ポート）
